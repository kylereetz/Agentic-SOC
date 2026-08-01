"""
Hardening test: validates that the Vault encrypts secrets at rest, fails safely when no key is
provided, and enforces role-based namespacing to prevent confused-deputy privilege escalation.
"""

import os
import json
import pytest
from cryptography.fernet import Fernet
from soc.security.vault import Vault


def test_vault_hardening(monkeypatch, tmp_path):
    # ── 1. Setup — generate an isolated key and temp path ───────────────────
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("SOC_VAULT_KEY", test_key)
    vault_path = str(tmp_path / "test_vault.enc")

    vault = Vault(vault_path, role="admin")
    secrets_payload = {
        "api_secret_key": "top-secret-hitl-token",
        "agents": {"scout": {"api_key": "old-key", "last_rotated": "never"}},
    }

    # ── 2. Save ──────────────────────────────────────────────────────────────
    vault.save(secrets_payload)

    # ── 3. Verify encryption — data on disk must not be plain-text JSON ──────
    with open(vault_path, "rb") as f:
        disk_data = f.read()

    print(f"Encrypted disk data length: {len(disk_data)}")
    with pytest.raises(Exception):
        json.loads(disk_data)
    print("[SUCCESS] Data is NOT plain-text JSON (encrypted).")

    # ── 4. Load & verify round-trip ──────────────────────────────────────────
    loaded = vault.load()
    assert loaded == secrets_payload, f"Decrypted payload mismatch: {loaded}"
    print("[SUCCESS] Vault decryption matches payload.")

    # ── 5. Fail-secure: no key should raise ValueError ───────────────────────
    monkeypatch.delenv("SOC_VAULT_KEY")
    with pytest.raises(ValueError, match="SOC_VAULT_KEY"):
        Vault(vault_path)
    print("[SUCCESS] Vault raised ValueError without key as expected.")

    # ── 6. Ephemeral namespacing — confused-deputy prevention ────────────────
    monkeypatch.setenv("SOC_VAULT_KEY", test_key)
    print("\n--- Testing Ephemeral Namespacing (Confused Deputy) ---")

    vault_admin = Vault(vault_path, role="admin")
    admin_data = vault_admin.load()
    assert (
        "api_secret_key" in admin_data
    ), "Admin Vault incorrectly stripped api_secret_key!"
    print("[SUCCESS] Admin Vault namespace correctly retained api_secret_key.")

    vault_scout = Vault(vault_path, role="scout")
    scout_data = vault_scout.load()
    assert (
        "api_secret_key" not in scout_data
    ), "Confused Deputy Vulnerability! Scout retained api_secret_key!"
    print("[SUCCESS] Scout Vault namespace correctly stripped api_secret_key.")


if __name__ == "__main__":
    test_vault_hardening()
