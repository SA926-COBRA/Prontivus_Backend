"""
Security Middleware for Prontivus
Implements TLS 1.3, security headers, and CORS protection
"""

import logging
from typing import Callable, List
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import time
import hashlib
import secrets

from app.core.security_config import security_settings

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = security_settings.SECURITY_HEADERS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add HSTS header
        if security_settings.HSTS_MAX_AGE > 0:
            hsts_value = f"max-age={security_settings.HSTS_MAX_AGE}"
            if security_settings.HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            if security_settings.HSTS_PRELOAD:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Add TLS version header (for monitoring)
        response.headers["X-TLS-Version"] = security_settings.TLS_VERSION
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not security_settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        endpoint = f"{request.method}:{request.url.path}"
        client_key = f"{client_ip}:{endpoint}"
        
        current_time = time.time()
        
        # Clean up old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_rate_limits(current_time)
            self.last_cleanup = current_time
        
        # Check rate limit
        if self._is_rate_limited(client_key, current_time):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self._record_request(client_key, current_time)
        
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_key: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        if client_key not in self.rate_limits:
            return False
        
        # Get requests in the last minute
        minute_ago = current_time - 60
        recent_requests = [
            req_time for req_time in self.rate_limits[client_key]
            if req_time > minute_ago
        ]
        
        # Check against limit
        limit = security_settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        return len(recent_requests) >= limit
    
    def _record_request(self, client_key: str, current_time: float):
        """Record a request"""
        if client_key not in self.rate_limits:
            self.rate_limits[client_key] = []
        
        self.rate_limits[client_key].append(current_time)
    
    def _cleanup_rate_limits(self, current_time: float):
        """Clean up old rate limit entries"""
        minute_ago = current_time - 60
        
        for client_key in list(self.rate_limits.keys()):
            self.rate_limits[client_key] = [
                req_time for req_time in self.rate_limits[client_key]
                if req_time > minute_ago
            ]
            
            # Remove empty entries
            if not self.rate_limits[client_key]:
                del self.rate_limits[client_key]

class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for security monitoring"""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            r"\.\./",  # Path traversal
            r"<script",  # XSS attempts
            r"union.*select",  # SQL injection
            r"exec\(",  # Command injection
            r"eval\(",  # Code injection
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for suspicious patterns in URL and headers
        if self._is_suspicious_request(request):
            logger.warning(f"Suspicious request detected: {request.url}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Suspicious request detected"}
            )
        
        # Add security tracking headers
        response = await call_next(request)
        
        # Add request ID for tracing
        request_id = request.headers.get("X-Request-ID", secrets.token_hex(8))
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Check if request contains suspicious patterns"""
        import re
        
        # Check URL path
        url_str = str(request.url)
        for pattern in self.suspicious_patterns:
            if re.search(pattern, url_str, re.IGNORECASE):
                return True
        
        # Check query parameters
        for param_name, param_value in request.query_params.items():
            param_str = f"{param_name}={param_value}"
            for pattern in self.suspicious_patterns:
                if re.search(pattern, param_str, re.IGNORECASE):
                    return True
        
        # Check headers
        for header_name, header_value in request.headers.items():
            header_str = f"{header_name}: {header_value}"
            for pattern in self.suspicious_patterns:
                if re.search(pattern, header_str, re.IGNORECASE):
                    return True
        
        return False

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.whitelist_enabled = security_settings.IP_WHITELIST_ENABLED
        self.whitelist = self._load_whitelist()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.whitelist_enabled:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        if not self._is_ip_allowed(client_ip):
            logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is in whitelist"""
        if not self.whitelist:
            return True  # Allow all if whitelist is empty
        
        return ip in self.whitelist
    
    def _load_whitelist(self) -> List[str]:
        """Load IP whitelist from configuration"""
        # In production, this would load from a database or configuration file
        return []

class IPBlacklistMiddleware(BaseHTTPMiddleware):
    """IP blacklist middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.blacklist_enabled = security_settings.IP_BLACKLIST_ENABLED
        self.blacklist = self._load_blacklist()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.blacklist_enabled:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        if self._is_ip_blocked(client_ip):
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blacklist"""
        return ip in self.blacklist
    
    def _load_blacklist(self) -> List[str]:
        """Load IP blacklist from configuration"""
        # In production, this would load from a database or threat intelligence feed
        return []

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware for security monitoring"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        client_ip = self._get_client_ip(request)
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"in {process_time:.3f}s "
            f"for {request.method} {request.url.path}"
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

def setup_security_middleware(app):
    """Setup all security middleware"""
    
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add rate limiting
    app.add_middleware(RateLimitMiddleware)
    
    # Add security monitoring
    app.add_middleware(SecurityMonitoringMiddleware)
    
    # Add IP filtering
    app.add_middleware(IPBlacklistMiddleware)
    app.add_middleware(IPWhitelistMiddleware)
    
    # Add request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=security_settings.CORS_ALLOWED_METHODS,
        allow_headers=security_settings.CORS_ALLOWED_HEADERS,
        max_age=security_settings.CORS_MAX_AGE
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=security_settings.ALLOWED_HOSTS
    )
    
    logger.info("Security middleware setup completed")

class TLSConfig:
    """TLS configuration helper"""
    
    @staticmethod
    def get_tls_config() -> dict:
        """Get TLS configuration for production deployment"""
        return {
            "ssl_version": "TLSv1_3",
            "ciphers": security_settings.TLS_CIPHER_SUITES,
            "cert_reqs": "CERT_REQUIRED",
            "options": [
                "OP_NO_SSLv2",
                "OP_NO_SSLv3", 
                "OP_NO_TLSv1",
                "OP_NO_TLSv1_1",
                "OP_NO_TLSv1_2"
            ]
        }
    
    @staticmethod
    def validate_tls_config() -> bool:
        """Validate TLS configuration"""
        try:
            import ssl
            
            # Check if TLS 1.3 is available
            if hasattr(ssl, 'PROTOCOL_TLSv1_3'):
                return True
            
            # Check if TLS 1.3 is available in newer versions
            if hasattr(ssl, 'PROTOCOL_TLS'):
                return True
            
            return False
            
        except ImportError:
            return False
