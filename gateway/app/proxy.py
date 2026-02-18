"""
HTTP Proxy service for forwarding requests to backend services.
"""

import asyncio
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urljoin

import httpx
from fastapi import Request, Response
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


class ProxyService:
    """
    Service for proxying HTTP requests to backend microservices.
    
    Features:
    - Request forwarding with header preservation
    - Response streaming
    - Timeout handling
    - Error handling
    """
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    async def start(self):
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.CONNECT_TIMEOUT,
                read=settings.REQUEST_TIMEOUT,
                write=settings.REQUEST_TIMEOUT,
                pool=settings.CONNECT_TIMEOUT
            ),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        logger.info("ProxyService started")
    
    async def stop(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("ProxyService stopped")
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, raising if not initialized."""
        if self._client is None:
            raise RuntimeError("ProxyService not started")
        return self._client
    
    def get_service_url(self, service: str) -> str:
        """Get base URL for a service."""
        services = {
            "pdf": settings.PDF_SERVICE_URL,
            "user": settings.USER_SERVICE_URL,
        }
        return services.get(service, settings.PDF_SERVICE_URL)
    
    def _prepare_headers(self, request: Request, extra_headers: Dict[str, str] = None) -> Dict[str, str]:
        """
        Prepare headers for proxied request.
        
        Preserves important headers but removes hop-by-hop headers.
        """
        # Headers to exclude (hop-by-hop)
        excluded = {
            "host", "connection", "keep-alive", "proxy-authenticate",
            "proxy-authorization", "te", "trailers", "transfer-encoding",
            "upgrade", "content-length"
        }
        
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in excluded
        }
        
        # Add X-Forwarded headers
        headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
        headers["X-Forwarded-Proto"] = request.url.scheme
        headers["X-Forwarded-Host"] = request.headers.get("host", "")
        
        # Add extra headers
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    async def proxy_request(
        self,
        request: Request,
        service: str,
        path: str,
        extra_headers: Dict[str, str] = None
    ) -> Response:
        """
        Proxy a request to a backend service.
        
        Args:
            request: FastAPI request
            service: Service name ("pdf" or "user")
            path: Path on the target service
            extra_headers: Additional headers to include
        
        Returns:
            FastAPI Response
        """
        service_url = self.get_service_url(service)
        target_url = urljoin(service_url, path)
        
        # Include query string
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"
        
        logger.info(
            "Proxying request",
            method=request.method,
            path=path,
            service=service,
            target=target_url
        )
        
        try:
            # Read request body
            body = await request.body()
            
            # Prepare headers
            headers = self._prepare_headers(request, extra_headers)
            
            # Make request
            response = await self.client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body
            )
            
            # Prepare response headers
            response_headers = dict(response.headers)
            # Remove hop-by-hop headers from response
            for header in ["transfer-encoding", "connection", "keep-alive"]:
                response_headers.pop(header, None)
            
            logger.info(
                "Proxy response",
                status=response.status_code,
                service=service,
                path=path
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type")
            )
            
        except httpx.ConnectError:
            logger.error("Service unavailable", service=service, url=target_url)
            return Response(
                content='{"error": "Service Unavailable", "message": "Backend service is not responding"}',
                status_code=503,
                media_type="application/json"
            )
        except httpx.TimeoutException:
            logger.error("Request timeout", service=service, url=target_url)
            return Response(
                content='{"error": "Gateway Timeout", "message": "Backend service timed out"}',
                status_code=504,
                media_type="application/json"
            )
        except Exception as e:
            logger.error("Proxy error", service=service, error=str(e))
            return Response(
                content=f'{{"error": "Gateway Error", "message": "{str(e)}"}}',
                status_code=502,
                media_type="application/json"
            )
    
    async def proxy_streaming(
        self,
        request: Request,
        service: str,
        path: str,
        extra_headers: Dict[str, str] = None
    ) -> StreamingResponse:
        """
        Proxy a request with streaming response.
        
        Used for SSE, file downloads, and other streaming endpoints.
        """
        service_url = self.get_service_url(service)
        target_url = urljoin(service_url, path)
        
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"
        
        try:
            body = await request.body()
            headers = self._prepare_headers(request, extra_headers)
            
            # Use stream context
            req = self.client.build_request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body
            )
            
            response = await self.client.send(req, stream=True)
            
            async def stream_content():
                try:
                    async for chunk in response.aiter_bytes():
                        yield chunk
                finally:
                    await response.aclose()
            
            return StreamingResponse(
                stream_content(),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
        except httpx.ConnectError:
            async def error_stream():
                yield b'{"error": "Service Unavailable"}'
            return StreamingResponse(error_stream(), status_code=503)
        except Exception as e:
            logger.error("Streaming proxy error", error=str(e))
            async def error_stream():
                yield f'{{"error": "{str(e)}"}}'.encode()
            return StreamingResponse(error_stream(), status_code=502)


# Singleton instance
proxy_service = ProxyService()
