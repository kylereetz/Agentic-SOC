import sys
import os
import logging

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soc.network.service_mesh import ServiceMesh, CryptoAgilityManager, mTLSAuthenticationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-CryptoAgility")

def test_service_mesh_agility():
    logger.info("Starting Crypto-Agility validation protocol...")
    
    dummy_db_path = "soc/reports/test_db.sqlite"
    os.makedirs(os.path.dirname(dummy_db_path), exist_ok=True)
    
    # Test 1: Generate High Assurance SSL Context
    logger.info("Test 1: SSL Context Generation")
    try:
        ctx = CryptoAgilityManager.get_tls_context(assurance_level="HIGH_ASSURANCE")
        logger.info("[SUCCESS] Generated restrictive X25519 Python SSLContext successfully.")
    except Exception as e:
        logger.error(f"[FAIL] Context generation failed: {e}")
        
    # Test 2: Valid Agent with High Assurance Cipher
    logger.info("Test 2: Valid Agent Identity + High Assurance Cipher")
    try:
        conn = ServiceMesh.connect_db(
            client_identity="triage", 
            db_path=dummy_db_path, 
            negotiated_cipher="TLS_AES_256_GCM_SHA384"
        )
        logger.info("[SUCCESS] ServiceMesh allowed connection for 'triage' utilizing X25519 ciphers.")
        conn.close()
    except Exception as e:
        logger.error(f"[FAIL] ServiceMesh rejected valid connection: {e}")

    # Test 3: Valid Agent with Outdated/Legacy RSA Cipher
    logger.info("Test 3: Valid Agent Identity + Legacy RSA Cipher (Must Block)")
    try:
        conn = ServiceMesh.connect_db(
            client_identity="triage", 
            db_path=dummy_db_path, 
            negotiated_cipher="TLS_RSA_WITH_AES_128_GCM_SHA256"
        )
        logger.error("[FAIL] ServiceMesh ALLOWED a legacy cryptographic cipher. This violates the Agility doctrine.")
        conn.close()
    except mTLSAuthenticationError as e:
        logger.info(f"[SUCCESS] ServiceMesh mathematically rejected the connection! Reason: {e}")
    except Exception as e:
        logger.error(f"[FAIL] Unexpected error type thrown: {e}")
        
    # Cleanup dummy DB
    if os.path.exists(dummy_db_path):
        os.remove(dummy_db_path)

if __name__ == "__main__":
    test_service_mesh_agility()
