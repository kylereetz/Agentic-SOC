"""
CAT (Cryptographic Action Token) Engine
Handles the generation and verification of HMAC-SHA256 signatures to securely
authenticate Human-in-the-Loop (HITL) execution commands, preventing webhook spoofing.
"""

import hmac
import hashlib


def sign_action(action_id: str, admin_secret: str) -> str:
    """
    Generates an HMAC-SHA256 signature for a specific action ID using the Vaulted admin secret.
    """
    if not admin_secret:
        raise ValueError("Admin secret cannot be empty for CAT generation.")

    # We use action_id as the payload for MVP. We can add more fields if needed.
    payload = action_id.encode("utf-8")
    secret_key = admin_secret.encode("utf-8")

    mac = hmac.new(secret_key, payload, hashlib.sha256)
    return mac.hexdigest()


def verify_cat(action_id: str, provided_cat: str, admin_secret: str) -> bool:
    """
    Verifies that the provided CAT matches the computed HMAC-SHA256 signature.
    """
    if not provided_cat or not admin_secret:
        return False

    expected_cat = sign_action(action_id, admin_secret)
    return hmac.compare_digest(expected_cat, provided_cat)
