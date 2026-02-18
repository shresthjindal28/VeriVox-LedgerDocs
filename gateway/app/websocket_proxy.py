"""
WebSocket proxy for real-time communication.
"""

import asyncio
from typing import Optional
from urllib.parse import urljoin, urlparse

import websockets
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class WebSocketProxy:
    """
    WebSocket proxy for forwarding WebSocket connections to backend services.
    """
    
    @staticmethod
    def get_ws_url(service: str, path: str) -> str:
        """Convert HTTP URL to WebSocket URL."""
        if service == "pdf":
            base_url = settings.PDF_SERVICE_URL
        else:
            base_url = settings.USER_SERVICE_URL
        
        # Convert http(s) to ws(s)
        parsed = urlparse(base_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = f"{ws_scheme}://{parsed.netloc}{path}"
        
        return ws_url
    
    @staticmethod
    async def proxy_websocket(
        client_ws: WebSocket,
        service: str,
        path: str,
        extra_headers: dict = None
    ):
        """
        Proxy WebSocket connection to backend service.
        
        Args:
            client_ws: Client WebSocket connection
            service: Backend service name
            path: WebSocket path on backend
            extra_headers: Additional headers (e.g., auth token)
        """
        target_url = WebSocketProxy.get_ws_url(service, path)
        
        logger.info(
            "Proxying WebSocket",
            service=service,
            path=path,
            target=target_url
        )
        
        # Accept client connection
        await client_ws.accept()
        
        # Prepare headers
        headers = {}
        if extra_headers:
            headers.update(extra_headers)
        
        # Forward auth header if present
        auth_header = client_ws.headers.get("authorization")
        if auth_header:
            headers["Authorization"] = auth_header
        
        try:
            async with websockets.connect(
                target_url,
                extra_headers=headers if headers else None,
                ping_interval=20,
                ping_timeout=10
            ) as backend_ws:
                
                # Create tasks for bidirectional forwarding
                async def forward_to_backend():
                    """Forward messages from client to backend."""
                    try:
                        while True:
                            data = await client_ws.receive_text()
                            await backend_ws.send(data)
                    except WebSocketDisconnect:
                        logger.info("Client disconnected")
                    except Exception as e:
                        logger.error(f"Error forwarding to backend: {e}")
                
                async def forward_to_client():
                    """Forward messages from backend to client."""
                    try:
                        async for message in backend_ws:
                            if client_ws.client_state == WebSocketState.CONNECTED:
                                await client_ws.send_text(message)
                    except Exception as e:
                        logger.error(f"Error forwarding to client: {e}")
                
                # Run both directions concurrently
                await asyncio.gather(
                    forward_to_backend(),
                    forward_to_client(),
                    return_exceptions=True
                )
                
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"WebSocket connection rejected: {e}")
            if client_ws.client_state == WebSocketState.CONNECTED:
                await client_ws.close(code=1008, reason="Backend rejected connection")
        except ConnectionRefusedError:
            logger.error("Backend WebSocket unavailable")
            if client_ws.client_state == WebSocketState.CONNECTED:
                await client_ws.close(code=1013, reason="Backend unavailable")
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
            if client_ws.client_state == WebSocketState.CONNECTED:
                await client_ws.close(code=1011, reason="Proxy error")
        finally:
            if client_ws.client_state == WebSocketState.CONNECTED:
                await client_ws.close()


websocket_proxy = WebSocketProxy()
