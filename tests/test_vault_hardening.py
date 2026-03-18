import os
import sys
import json
from soc.security.vault import Vault
from cryptography.fernet import Fernet

def test_vault_hardening():
    # 1. Setup a test key
    test_key = Fernet.generate_key().decode()
    os.environ["SOC_VAULT_KEY"] = test_key
    
    vault_path = "tests/test_vault.enc"
    if os.path.exists(vault_path):
        os.remove(vault_path)
        
    vault = Vault(vault_path)
    secrets_payload = {
        "agents": {
            "scout": {"api_key": "old-key", "last_rotated": "never"}
        }
    }
    
    # 2. SAVE
    vault.save(secrets_payload)
    
    # 3. VERIFY ENCRYPTION
    with open(vault_path, "rb") as f:
        disk_data = f.read()
        
    print(f"Encrypted disk data length: {len(disk_data)}")
    try:
        json.loads(disk_data)
        print("[FAILURE] Data is plain-text JSON on disk!")
        sys.exit(1)
    except:
        print("[SUCCESS] Data is NOT plain-text JSON (encrypted).")
        
    # 4. LOAD
    loaded = vault.load()
    print(f"Loaded: {loaded}")
    if loaded == secrets_payload:
        print("[SUCCESS] Vault decryption matches payload.")
    else:
        print("[FAILURE] Decrypted payload mismatch!")
        sys.exit(1)

    # 5. NO KEY TEST (Should fail to decrypt or return empty)
    os.environ.pop("SOC_VAULT_KEY")
    vault_no_key = Vault(vault_path)
    try:
        fail_load = vault_no_key.load()
        # If no key is provided, Vault might try to load as plain text or fail.
        # Given current implementation, if no key, it attempts json.loads(raw_data)
        # which will fail for encrypted data.
        print(f"Load without key: {fail_load}")
        if not fail_load:
            print("[SUCCESS] Vault safely returned empty/failed on encrypted data without key.")
        else:
            print("[FAILURE] Vault returned data without a key?")
            sys.exit(1)
    except Exception as e:
        print(f"[SUCCESS] Vault raised error without key: {e}")

if __name__ == "__main__":
    test_vault_hardening()
