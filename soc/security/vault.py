import os
import json
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger("RCA-Vault")

class Vault:
    """
    Secure storage for SOC secrets.
    Encrypts data at rest using AES-256 (Fernet).
    """
    def __init__(self, vault_path: str, role: str = "default"):
        self.vault_path = vault_path
        self.vault_key = os.environ.get("SOC_VAULT_KEY")
        self.cipher = None
        self.role = role

        if self.vault_key:
            try:
                self.cipher = Fernet(self.vault_key.encode())
            except Exception as e:
                logger.error(f"Invalid SOC_VAULT_KEY: {e}")
        else:
            logger.warning("SOC_VAULT_KEY NOT FOUND. Vault will operate in UNRESTRICTED mode (Plain-text).")

    def load(self) -> dict:
        """Load and decrypt the vault content."""
        if not os.path.exists(self.vault_path):
            return {}

        try:
            with open(self.vault_path, "rb") as f:
                raw_data = f.read()

            if not raw_data:
                return {}

            if self.cipher:
                # Attempt to decrypt
                try:
                    decrypted_data = self.cipher.decrypt(raw_data)
                    return self._namespace_data(json.loads(decrypted_data))
                except Exception:
                    # If decryption fails but we have a key, it might be a newly set key on old data 
                    # or the data is plain-text. 
                    logger.error("Decryption failed. Data might be corrupted or key is incorrect.")
                    return {}
            else:
                # Fallback to plain-text JSON if no cipher
                return self._namespace_data(json.loads(raw_data))
        except Exception as e:
            logger.error(f"Failed to load vault: {e}")
            return {}

    def _namespace_data(self, data: dict) -> dict:
        """[SECURITY] Enforces Ephemeral Namespacing by stripping unauthorized keys."""
        ADMIN_ROLES = {"admin", "api", "orchestrator", "responder"}
        
        if self.role not in ADMIN_ROLES:
            # Strip highly sensitive tokens from standard worker agents (Confused Deputy Prevention)
            data.pop("api_secret_key", None)
            
        return data

    def save(self, data: dict):
        """Encrypt and save data to the vault."""
        try:
            raw_json = json.dumps(data, indent=2).encode()
            
            if self.cipher:
                encrypted_data = self.cipher.encrypt(raw_json)
                with open(self.vault_path, "wb") as f:
                    f.write(encrypted_data)
            else:
                with open(self.vault_path, "wb") as f:
                    f.write(raw_json)
            
            # Restrict permissions (Unix-like systems)
            try:
                os.chmod(self.vault_path, 0o600)
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to save vault: {e}")
