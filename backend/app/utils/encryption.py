"""
Encryption utilities for API keys and sensitive data

Provides functions to encrypt/decrypt API keys at rest and manage key rotation.

Validates: Requirements 17.5, 20.4
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manager for encrypting and decrypting sensitive data
    
    Validates: Requirements 17.5, 20.4
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            master_key: Master encryption key (from environment variable)
        """
        # Get master key from environment or generate one
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        
        if not self.master_key:
            logger.warning(
                "No ENCRYPTION_MASTER_KEY found in environment. "
                "Generating a temporary key. This should not be used in production!"
            )
            self.master_key = Fernet.generate_key().decode()
        
        # Derive encryption key from master key
        self.fernet = self._create_fernet(self.master_key)
    
    def _create_fernet(self, master_key: str) -> Fernet:
        """
        Create a Fernet cipher from master key
        
        Args:
            master_key: Master key string
            
        Returns:
            Fernet cipher instance
        """
        # Use PBKDF2HMAC to derive a key from the master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'sva_chatbot_salt',  # In production, use a random salt stored securely
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
            
        Validates: Requirements 17.5, 20.4
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        
        try:
            encrypted_bytes = self.fernet.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            ciphertext: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plaintext string
            
        Validates: Requirements 17.5, 20.4
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty string")
        
        try:
            decrypted_bytes = self.fernet.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def rotate_key(self, new_master_key: str) -> 'EncryptionManager':
        """
        Rotate to a new master key
        
        Args:
            new_master_key: New master key
            
        Returns:
            New EncryptionManager with new key
            
        Validates: Requirement 20.4
        """
        logger.info("Rotating encryption key")
        return EncryptionManager(new_master_key)
    
    def re_encrypt_with_new_key(
        self,
        ciphertext: str,
        new_manager: 'EncryptionManager'
    ) -> str:
        """
        Re-encrypt data with a new key
        
        Args:
            ciphertext: Data encrypted with old key
            new_manager: EncryptionManager with new key
            
        Returns:
            Data encrypted with new key
            
        Validates: Requirement 20.4
        """
        # Decrypt with old key
        plaintext = self.decrypt(ciphertext)
        
        # Encrypt with new key
        return new_manager.encrypt(plaintext)


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """
    Get the global encryption manager instance
    
    Returns:
        EncryptionManager instance
    """
    global _encryption_manager
    
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    
    return _encryption_manager


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage
    
    Args:
        api_key: Plaintext API key
        
    Returns:
        Encrypted API key
        
    Validates: Requirements 17.5, 20.4
    """
    manager = get_encryption_manager()
    return manager.encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key from storage
    
    Args:
        encrypted_key: Encrypted API key
        
    Returns:
        Plaintext API key
        
    Validates: Requirements 17.5, 20.4
    """
    manager = get_encryption_manager()
    return manager.decrypt(encrypted_key)


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key for display/logging
    
    Args:
        api_key: API key to mask
        visible_chars: Number of characters to show at end
        
    Returns:
        Masked API key (e.g., "****abcd")
        
    Validates: Requirement 17.5
    """
    if not api_key or len(api_key) <= visible_chars:
        return "****"
    
    return "*" * (len(api_key) - visible_chars) + api_key[-visible_chars:]


def generate_encryption_key() -> str:
    """
    Generate a new encryption key
    
    Returns:
        Base64-encoded encryption key
        
    Note: This should be stored securely in environment variables
    """
    return Fernet.generate_key().decode()


class SecureAPIKeyStore:
    """
    Secure storage for API keys with encryption
    
    Validates: Requirements 17.5, 20.4
    """
    
    def __init__(self, db):
        """
        Initialize secure API key store
        
        Args:
            db: Database instance
        """
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    async def store_api_key(
        self,
        user_id: str,
        service_name: str,
        api_key: str
    ) -> str:
        """
        Store an API key securely
        
        Args:
            user_id: User ID
            service_name: Name of the service (e.g., 'groq')
            api_key: Plaintext API key
            
        Returns:
            Key ID
            
        Validates: Requirements 17.5, 20.4
        """
        # Encrypt the API key
        encrypted_key = self.encryption_manager.encrypt(api_key)
        
        # Store in database
        result = await self.db.api_keys.insert_one({
            'user_id': user_id,
            'service_name': service_name,
            'encrypted_key': encrypted_key,
            'created_at': datetime.utcnow(),
            'last_rotated': datetime.utcnow()
        })
        
        logger.info(
            f"API key stored for user {user_id}, service {service_name}"
        )
        
        return str(result.inserted_id)
    
    async def retrieve_api_key(
        self,
        user_id: str,
        service_name: str
    ) -> Optional[str]:
        """
        Retrieve and decrypt an API key
        
        Args:
            user_id: User ID
            service_name: Name of the service
            
        Returns:
            Decrypted API key or None if not found
            
        Validates: Requirements 17.5, 20.4
        """
        # Find the key in database
        key_doc = await self.db.api_keys.find_one({
            'user_id': user_id,
            'service_name': service_name
        })
        
        if not key_doc:
            return None
        
        # Decrypt and return
        encrypted_key = key_doc['encrypted_key']
        return self.encryption_manager.decrypt(encrypted_key)
    
    async def rotate_api_key(
        self,
        user_id: str,
        service_name: str,
        new_api_key: str
    ) -> bool:
        """
        Rotate an API key
        
        Args:
            user_id: User ID
            service_name: Name of the service
            new_api_key: New plaintext API key
            
        Returns:
            True if successful
            
        Validates: Requirement 20.4
        """
        # Encrypt the new key
        encrypted_key = self.encryption_manager.encrypt(new_api_key)
        
        # Update in database
        result = await self.db.api_keys.update_one(
            {
                'user_id': user_id,
                'service_name': service_name
            },
            {
                '$set': {
                    'encrypted_key': encrypted_key,
                    'last_rotated': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(
                f"API key rotated for user {user_id}, service {service_name}"
            )
            return True
        
        return False
    
    async def delete_api_key(
        self,
        user_id: str,
        service_name: str
    ) -> bool:
        """
        Delete an API key
        
        Args:
            user_id: User ID
            service_name: Name of the service
            
        Returns:
            True if successful
        """
        result = await self.db.api_keys.delete_one({
            'user_id': user_id,
            'service_name': service_name
        })
        
        return result.deleted_count > 0


# Import datetime for timestamps
from datetime import datetime
