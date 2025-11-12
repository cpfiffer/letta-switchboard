import pytest
import os
from cryptography.fernet import Fernet
from crypto_utils import (
    get_api_key_hash,
    is_dev_mode,
    get_encryption_key,
    encrypt_json,
    decrypt_json,
)


class TestApiKeyHash:
    def test_hash_is_deterministic(self):
        """Same API key should produce same hash."""
        api_key = "test-key-123"
        hash1 = get_api_key_hash(api_key)
        hash2 = get_api_key_hash(api_key)
        assert hash1 == hash2
    
    def test_hash_is_16_chars(self):
        """Hash should be 16 characters long."""
        api_key = "test-key-123"
        hash_val = get_api_key_hash(api_key)
        assert len(hash_val) == 16
    
    def test_different_keys_different_hashes(self):
        """Different API keys should produce different hashes."""
        hash1 = get_api_key_hash("key1")
        hash2 = get_api_key_hash("key2")
        assert hash1 != hash2


class TestDevMode:
    def test_dev_mode_true(self):
        """Dev mode should be enabled when env var is 'true'."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "true"
        assert is_dev_mode() is True
    
    def test_dev_mode_1(self):
        """Dev mode should be enabled when env var is '1'."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "1"
        assert is_dev_mode() is True
    
    def test_dev_mode_yes(self):
        """Dev mode should be enabled when env var is 'yes'."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "yes"
        assert is_dev_mode() is True
    
    def test_dev_mode_false(self):
        """Dev mode should be disabled when env var is 'false'."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "false"
        assert is_dev_mode() is False
    
    def test_dev_mode_unset(self):
        """Dev mode should be disabled when env var is not set."""
        if "LETTA_SWITCHBOARD_DEV_MODE" in os.environ:
            del os.environ["LETTA_SWITCHBOARD_DEV_MODE"]
        assert is_dev_mode() is False


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self, encryption_key):
        """Data should survive encryption/decryption roundtrip."""
        original_data = {
            "id": "test-123",
            "message": "Hello world",
            "nested": {"key": "value"}
        }
        
        encrypted = encrypt_json(original_data, encryption_key)
        decrypted = decrypt_json(encrypted, encryption_key)
        
        assert decrypted == original_data
    
    def test_encrypted_data_is_bytes(self, encryption_key):
        """Encrypted data should be bytes."""
        data = {"test": "data"}
        encrypted = encrypt_json(data, encryption_key)
        assert isinstance(encrypted, bytes)
    
    def test_dev_mode_plaintext(self):
        """In dev mode, data should be plaintext JSON."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "true"
        
        data = {"test": "data", "number": 123}
        key = b"ignored-in-dev-mode"
        
        encrypted = encrypt_json(data, key)
        assert isinstance(encrypted, bytes)
        
        # Should be valid JSON
        import json
        parsed = json.loads(encrypted)
        assert parsed == data
    
    def test_dev_mode_decrypt(self):
        """In dev mode, decrypt should parse plaintext JSON."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "true"
        
        data = {"test": "data"}
        key = b"ignored"
        
        encrypted = encrypt_json(data, key)
        decrypted = decrypt_json(encrypted, key)
        
        assert decrypted == data
    
    def test_production_mode_encrypted(self):
        """In production mode, data should be encrypted (not plaintext)."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "false"
        
        data = {"test": "secret"}
        key = Fernet.generate_key()
        
        encrypted = encrypt_json(data, key)
        
        # Should NOT be valid JSON
        import json
        with pytest.raises(json.JSONDecodeError):
            json.loads(encrypted)
    
    def test_wrong_key_fails(self, encryption_key):
        """Decrypting with wrong key should fail."""
        os.environ["LETTA_SWITCHBOARD_DEV_MODE"] = "false"
        
        data = {"test": "data"}
        encrypted = encrypt_json(data, encryption_key)
        
        wrong_key = Fernet.generate_key()
        
        with pytest.raises(Exception):
            decrypt_json(encrypted, wrong_key)
