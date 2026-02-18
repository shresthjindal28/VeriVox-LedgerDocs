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
    async def _proxy_messages(client_ws: WebSocket, backend_ws):
        """Helper method to proxy messages between client and backend."""
        # Create tasks for bidirectional forwarding
        async def forward_to_backend():
            """Forward messages from client to backend."""
            try:
                while True:
                    data = await client_ws.receive_text()
                    # Log start_call messages for debugging
                    try:
                        import json
                        msg = json.loads(data)
                        msg_type = msg.get("type")
                        if msg_type == "start_call":
                            logger.info("Forwarding start_call message to backend", message_preview=data[:100])
                        else:
                            logger.debug(f"Forwarding message type: {msg_type}", message_preview=data[:100])
                    except Exception as e:
                        logger.debug(f"Non-JSON message or parse error: {e}", message_preview=data[:100])
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
            # Prepare connection kwargs
            connect_kwargs = {
                "ping_interval": 20,
                "ping_timeout": 10
            }
            
            # Add headers if provided (websockets 16 accepts dict or HeadersLike)
            if headers:
                connect_kwargs["additional_headers"] = headers
            
            # Connect - handle case where headers might not be supported
            # TypeError occurs when entering the async context manager, not when creating it
            try:
                async with websockets.connect(target_url, **connect_kwargs) as backend_ws:
                    await WebSocketProxy._proxy_messages(client_ws, backend_ws)
            except TypeError as e:
                # If headers caused the error, retry without them
                if headers and ("additional_headers" in str(e) or "extra_headers" in str(e) or "unexpected keyword" in str(e)):
                    logger.warning("WebSocket headers not supported, connecting without custom headers")
                    connect_kwargs.pop("additional_headers", None)
                    async with websockets.connect(target_url, **connect_kwargs) as backend_ws:
                        await WebSocketProxy._proxy_messages(client_ws, backend_ws)
                else:
                    raise
                
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"WebSocket connection rejected: {e}")
            if client_ws.client_state == WebSocketState.CONNECTED:
                try:
                    await client_ws.close(code=1008, reason="Backend rejected connection")
                except RuntimeError:
                    pass  # Already closed
        except ConnectionRefusedError:
            logger.error("Backend WebSocket unavailable")
            if client_ws.client_state == WebSocketState.CONNECTED:
                try:
                    await client_ws.close(code=1013, reason="Backend unavailable")
                except RuntimeError:
                    pass  # Already closed
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
            if client_ws.client_state == WebSocketState.CONNECTED:
                try:
                    await client_ws.close(code=1011, reason="Proxy error")
                except RuntimeError:
                    pass  # Already closed
        finally:
            # Only close if still connected and not already closed
            if client_ws.client_state == WebSocketState.CONNECTED:
                try:
                    await client_ws.close()
                except RuntimeError:
                    pass  # Already closed


websocket_proxy = WebSocketProxy()
