"""
AES-256 Encryption Service for Prontivus
Implements AES-256-GCM encryption for data at rest
"""

import base64
import secrets
from typing import Any, Dict, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import json
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """AES-256 encryption service for sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service
        
        Args:
            encryption_key: Base64 encoded encryption key. If None, generates a new one.
        """
        if encryption_key:
            self.key = base64.urlsafe_b64decode(encryption_key.encode())
        else:
            # Generate a new 256-bit key
            self.key = secrets.token_bytes(32)
        
        # Ensure key is exactly 32 bytes for AES-256
        if len(self.key) != 32:
            raise ValueError("Encryption key must be 32 bytes (256 bits)")
    
    def encrypt_data(self, data: Union[str, Dict, Any]) -> str:
        """
        Encrypt data using AES-256-GCM
        
        Args:
            data: Data to encrypt (string, dict, or any JSON-serializable object)
            
        Returns:
            Base64 encoded encrypted data with IV and tag
        """
        try:
            # Convert data to JSON string if it's not already a string
            if isinstance(data, str):
                data_str = data
            else:
                data_str = json.dumps(data, ensure_ascii=False)
            
            # Generate random IV
            iv = secrets.token_bytes(12)  # 96-bit IV for GCM
            
            # Create cipher
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv))
            encryptor = cipher.encryptor()
            
            # Encrypt data
            encrypted_data = encryptor.update(data_str.encode('utf-8')) + encryptor.finalize()
            
            # Combine IV + encrypted data + tag
            combined = iv + encryptor.tag + encrypted_data
            
            # Return base64 encoded result
            return base64.urlsafe_b64encode(combined).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt_data(self, encrypted_data: str) -> Union[str, Dict, Any]:
        """
        Decrypt data using AES-256-GCM
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted data (string or parsed JSON)
        """
        try:
            # Decode base64
            combined = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Extract IV, tag, and encrypted data
            iv = combined[:12]  # First 12 bytes are IV
            tag = combined[12:28]  # Next 16 bytes are tag
            encrypted = combined[28:]  # Rest is encrypted data
            
            # Create cipher
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv, tag))
            decryptor = cipher.decryptor()
            
            # Decrypt data
            decrypted_bytes = decryptor.update(encrypted) + decryptor.finalize()
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON, return string if it fails
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
                
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_field(self, field_value: Any) -> Optional[str]:
        """
        Encrypt a single field value
        
        Args:
            field_value: Value to encrypt
            
        Returns:
            Encrypted value or None if input is None/empty
        """
        if field_value is None or field_value == "":
            return None
        
        return self.encrypt_data(str(field_value))
    
    def decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """
        Decrypt a single field value
        
        Args:
            encrypted_value: Encrypted value to decrypt
            
        Returns:
            Decrypted value or None if input is None/empty
        """
        if encrypted_value is None or encrypted_value == "":
            return None
        
        try:
            decrypted = self.decrypt_data(encrypted_value)
            return str(decrypted) if decrypted is not None else None
        except Exception as e:
            logger.error(f"Field decryption failed: {str(e)}")
            return None
    
    def encrypt_pii(self, pii_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Encrypt PII (Personally Identifiable Information) fields
        
        Args:
            pii_data: Dictionary containing PII fields
            
        Returns:
            Dictionary with encrypted PII fields
        """
        encrypted_pii = {}
        
        # Fields that should be encrypted
        pii_fields = [
            'cpf', 'rg', 'passport', 'phone', 'email', 'address',
            'birth_date', 'mother_name', 'father_name', 'emergency_contact',
            'insurance_number', 'medical_record_number'
        ]
        
        for field, value in pii_data.items():
            if field.lower() in pii_fields and value is not None:
                encrypted_pii[field] = self.encrypt_field(value)
            else:
                encrypted_pii[field] = value
        
        return encrypted_pii
    
    def decrypt_pii(self, encrypted_pii_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt PII fields
        
        Args:
            encrypted_pii_data: Dictionary containing encrypted PII fields
            
        Returns:
            Dictionary with decrypted PII fields
        """
        decrypted_pii = {}
        
        for field, value in encrypted_pii_data.items():
            if isinstance(value, str) and value.startswith('encrypted:'):
                # Remove 'encrypted:' prefix if present
                encrypted_value = value.replace('encrypted:', '')
                decrypted_pii[field] = self.decrypt_field(encrypted_value)
            else:
                decrypted_pii[field] = value
        
        return decrypted_pii
    
    def generate_key(self) -> str:
        """
        Generate a new encryption key
        
        Returns:
            Base64 encoded encryption key
        """
        new_key = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(new_key).decode('utf-8')
    
    def rotate_key(self, old_key: str, new_key: str) -> Dict[str, Any]:
        """
        Rotate encryption key (for future implementation)
        
        Args:
            old_key: Current encryption key
            new_key: New encryption key
            
        Returns:
            Status of key rotation
        """
        # This would require re-encrypting all existing data
        # Implementation depends on database migration strategy
        return {
            "status": "not_implemented",
            "message": "Key rotation requires data migration"
        }
    
    def verify_encryption(self, data: str, encrypted_data: str) -> bool:
        """
        Verify that encryption/decryption works correctly
        
        Args:
            data: Original data
            encrypted_data: Encrypted data
            
        Returns:
            True if decryption matches original data
        """
        try:
            decrypted = self.decrypt_data(encrypted_data)
            return str(decrypted) == str(data)
        except Exception:
            return False

class FieldEncryptionMixin:
    """Mixin for SQLAlchemy models to handle field encryption"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encryption_service = EncryptionService()
    
    def encrypt_field_value(self, field_name: str, value: Any) -> Optional[str]:
        """Encrypt a field value"""
        return self._encryption_service.encrypt_field(value)
    
    def decrypt_field_value(self, field_name: str, encrypted_value: str) -> Optional[str]:
        """Decrypt a field value"""
        return self._encryption_service.decrypt_field(encrypted_value)
    
    def get_encrypted_fields(self) -> list:
        """Get list of fields that should be encrypted"""
        return getattr(self, '_encrypted_fields', [])
    
    def before_save(self):
        """Called before saving - encrypt sensitive fields"""
        encrypted_fields = self.get_encrypted_fields()
        for field_name in encrypted_fields:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                if value is not None:
                    encrypted_value = self.encrypt_field_value(field_name, value)
                    setattr(self, f"{field_name}_encrypted", encrypted_value)
                    # Clear the original value for security
                    setattr(self, field_name, None)
    
    def after_load(self):
        """Called after loading - decrypt sensitive fields"""
        encrypted_fields = self.get_encrypted_fields()
        for field_name in encrypted_fields:
            encrypted_field_name = f"{field_name}_encrypted"
            if hasattr(self, encrypted_field_name):
                encrypted_value = getattr(self, encrypted_field_name)
                if encrypted_value is not None:
                    decrypted_value = self.decrypt_field_value(field_name, encrypted_value)
                    setattr(self, field_name, decrypted_value)

# Global encryption service instance
encryption_service = EncryptionService()
