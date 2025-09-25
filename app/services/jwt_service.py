"""
Enhanced JWT Service with 2FA Support for Prontivus
Implements secure JWT tokens with two-factor authentication
"""

import secrets
import pyotp
import qrcode
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from jose import JWTError, jwt
from io import BytesIO
import base64
import hashlib
import uuid
import logging

from app.core.security_config import security_settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import Token, TokenData, TwoFactorSetup

logger = logging.getLogger(__name__)

class EnhancedJWTService:
    """Enhanced JWT service with 2FA support"""
    
    def __init__(self):
        self.secret_key = security_settings.get_jwt_secret()
        self.algorithm = security_settings.JWT_ALGORITHM
        self.issuer = security_settings.JWT_ISSUER
        self.audience = security_settings.JWT_AUDIENCE
        self.access_token_expire_minutes = security_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = security_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
        requires_2fa: bool = False,
        session_id: Optional[str] = None
    ) -> str:
        """
        Create enhanced access token
        
        Args:
            data: Token payload data
            expires_delta: Custom expiration time
            requires_2fa: Whether 2FA is required
            session_id: Session ID for tracking
            
        Returns:
            JWT access token
        """
        to_encode = data.copy()
        
        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        # Enhanced token claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": self.issuer,
            "aud": self.audience,
            "jti": str(uuid.uuid4()),  # JWT ID for token tracking
            "type": "access",
            "requires_2fa": requires_2fa,
            "session_id": session_id or str(uuid.uuid4()),
            "version": "2.0"  # Token version for future compatibility
        })
        
        # Add security fingerprint
        if "user_id" in data:
            to_encode["fingerprint"] = self._generate_fingerprint(data["user_id"], session_id)
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """
        Create enhanced refresh token
        
        Args:
            data: Token payload data
            session_id: Session ID for tracking
            
        Returns:
            JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        # Enhanced refresh token claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": self.issuer,
            "aud": self.audience,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
            "session_id": session_id or str(uuid.uuid4()),
            "version": "2.0"
        })
        
        # Add security fingerprint
        if "user_id" in data:
            to_encode["fingerprint"] = self._generate_fingerprint(data["user_id"], session_id)
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """
        Verify and decode token with enhanced security checks
        
        Args:
            token: JWT token to verify
            
        Returns:
            TokenData object
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            
            # Extract required fields
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            tenant_id: Optional[int] = payload.get("tenant_id")
            token_type: str = payload.get("type", "access")
            requires_2fa: bool = payload.get("requires_2fa", False)
            session_id: str = payload.get("session_id")
            fingerprint: str = payload.get("fingerprint")
            
            if username is None or user_id is None:
                raise AuthenticationError("Invalid token payload")
            
            # Verify fingerprint for additional security
            if fingerprint and not self._verify_fingerprint(user_id, session_id, fingerprint):
                raise AuthenticationError("Token fingerprint mismatch")
            
            return TokenData(
                username=username,
                user_id=user_id,
                tenant_id=tenant_id,
                token_type=token_type,
                requires_2fa=requires_2fa,
                session_id=session_id
            )
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise AuthenticationError("Token verification failed")
    
    def verify_refresh_token(self, token: str) -> TokenData:
        """
        Verify refresh token specifically
        
        Args:
            token: Refresh token to verify
            
        Returns:
            TokenData object
        """
        token_data = self.verify_token(token)
        
        if token_data.token_type != "refresh":
            raise AuthenticationError("Invalid refresh token type")
        
        return token_data
    
    def create_2fa_token(self, user_id: int, session_id: str) -> str:
        """
        Create temporary token for 2FA verification
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Temporary 2FA token
        """
        data = {
            "sub": f"2fa_{user_id}",
            "user_id": user_id,
            "type": "2fa_temp",
            "session_id": session_id
        }
        
        # Short-lived token (5 minutes)
        expires_delta = timedelta(minutes=5)
        
        return self.create_access_token(data, expires_delta=expires_delta)
    
    def verify_2fa_token(self, token: str) -> TokenData:
        """
        Verify 2FA temporary token
        
        Args:
            token: 2FA token to verify
            
        Returns:
            TokenData object
        """
        token_data = self.verify_token(token)
        
        if token_data.token_type != "2fa_temp":
            raise AuthenticationError("Invalid 2FA token type")
        
        return token_data
    
    def rotate_tokens(
        self,
        refresh_token: str,
        user_id: int,
        session_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Rotate tokens (create new access and refresh tokens)
        
        Args:
            refresh_token: Current refresh token
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dictionary with new tokens
        """
        # Verify current refresh token
        token_data = self.verify_refresh_token(refresh_token)
        
        if token_data.user_id != user_id:
            raise AuthenticationError("Token user mismatch")
        
        # Create new tokens
        new_session_id = session_id or str(uuid.uuid4())
        
        access_data = {
            "sub": token_data.username,
            "user_id": user_id,
            "tenant_id": token_data.tenant_id
        }
        
        refresh_data = {
            "sub": token_data.username,
            "user_id": user_id,
            "tenant_id": token_data.tenant_id
        }
        
        new_access_token = self.create_access_token(access_data, session_id=new_session_id)
        new_refresh_token = self.create_refresh_token(refresh_data, session_id=new_session_id)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "session_id": new_session_id
        }
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (add to blacklist)
        
        Args:
            token: Token to revoke
            
        Returns:
            True if successful
        """
        try:
            # In a production system, you would add this token to a blacklist
            # For now, we'll just log the revocation
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get("jti")
            
            logger.info(f"Token revoked: {jti}")
            return True
            
        except Exception as e:
            logger.error(f"Token revocation failed: {str(e)}")
            return False
    
    def _generate_fingerprint(self, user_id: int, session_id: Optional[str]) -> str:
        """
        Generate security fingerprint for token
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Security fingerprint
        """
        data = f"{user_id}:{session_id}:{self.secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _verify_fingerprint(self, user_id: int, session_id: str, fingerprint: str) -> bool:
        """
        Verify security fingerprint
        
        Args:
            user_id: User ID
            session_id: Session ID
            fingerprint: Fingerprint to verify
            
        Returns:
            True if fingerprint is valid
        """
        expected_fingerprint = self._generate_fingerprint(user_id, session_id)
        return fingerprint == expected_fingerprint

class TwoFactorService:
    """Two-Factor Authentication service"""
    
    def __init__(self):
        self.issuer = security_settings.TOTP_ISSUER
        self.window = security_settings.TOTP_WINDOW
        self.secret_length = security_settings.TOTP_SECRET_LENGTH
        self.backup_codes_count = security_settings.BACKUP_CODES_COUNT
        self.backup_code_length = security_settings.BACKUP_CODE_LENGTH
    
    def generate_secret(self) -> str:
        """
        Generate TOTP secret
        
        Returns:
            Base32 encoded secret
        """
        return pyotp.random_base32(length=self.secret_length)
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """
        Generate QR code for 2FA setup
        
        Args:
            user_email: User email
            secret: TOTP secret
            
        Returns:
            Base64 encoded QR code image
        """
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_totp_code(self, secret: str, code: str) -> bool:
        """
        Verify TOTP code
        
        Args:
            secret: TOTP secret
            code: Code to verify
            
        Returns:
            True if code is valid
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=self.window)
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for 2FA
        
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(self.backup_codes_count):
            code = secrets.token_hex(self.backup_code_length // 2).upper()
            codes.append(code)
        return codes
    
    def verify_backup_code(self, code: str, stored_codes: List[str]) -> bool:
        """
        Verify backup code
        
        Args:
            code: Code to verify
            stored_codes: List of stored backup codes
            
        Returns:
            True if code is valid
        """
        return code.upper() in [c.upper() for c in stored_codes]
    
    def setup_2fa(self, user_email: str) -> TwoFactorSetup:
        """
        Setup 2FA for user
        
        Args:
            user_email: User email
            
        Returns:
            TwoFactorSetup object with secret and QR code
        """
        secret = self.generate_secret()
        qr_code_url = self.generate_qr_code(user_email, secret)
        backup_codes = self.generate_backup_codes()
        
        return TwoFactorSetup(
            secret=secret,
            qr_code_url=f"data:image/png;base64,{qr_code_url}",
            backup_codes=backup_codes
        )
    
    def verify_2fa_setup(self, secret: str, code: str) -> bool:
        """
        Verify 2FA setup code
        
        Args:
            secret: TOTP secret
            code: Verification code
            
        Returns:
            True if setup is valid
        """
        return self.verify_totp_code(secret, code)

# Global service instances
jwt_service = EnhancedJWTService()
two_factor_service = TwoFactorService()
