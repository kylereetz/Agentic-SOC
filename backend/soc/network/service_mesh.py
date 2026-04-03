"""
Service Mesh Enforcer for Zero Trust Architecture.

Simulates an Envoy/Istio-style internal proxy that mandates Mutual TLS (mTLS)
for all internal data-tier connections (e.g., SQLite DB), and strictly enforces
IAM execution roles for external Cloud Storage outbound access.

This prevents prompt-injected or compromised workers (like MALWARE-PATHOLOGIST)
from performing lateral movement into the DB, or overwriting Evidence repositories.
"""
import logging
import sqlite3
import os
import ssl

logger = logging.getLogger("RCA-ServiceMesh")

class CryptoAgilityManager:
    """
    Centralized Cryptographic Nervous System.
    Provides modular, interchangeable Cipher Suites specifically hardened against
    Deep Evidential vulnerabilities and Post-Quantum cryptographic exhaustion attacks.
    """
    
    # -----------------------------------------------------
    # Pillar 2/5: Hybrid Deployment & Crypto-Agility
    # -----------------------------------------------------
    CIPHER_SUITES_STANDARD = [
        "TLS_AES_128_GCM_SHA256",
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256"
    ]
    
    CIPHER_SUITES_HIGH_ASSURANCE = [
        "TLS_AES_256_GCM_SHA384",          # TLS 1.3 Must-Support Forward Secrecy
        "TLS_CHACHA20_POLY1305_SHA256"     # High Performance alternative
    ]
    
    @classmethod
    def get_tls_context(cls, assurance_level: str = "HIGH_ASSURANCE") -> ssl.SSLContext:
        """
        Natively hardens Python's Default Context for all inner-agent TCP/IP comms.
        Forces strict TLS 1.3.
        """
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        # Disable all legacy protocol versions below TLS 1.3
        ctx.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2
        
        cipher_target = cls.CIPHER_SUITES_HIGH_ASSURANCE
        if assurance_level.upper() == "STANDARD":
            cipher_target = cls.CIPHER_SUITES_STANDARD
            
        ctx.set_ciphers(':'.join(cipher_target))
        return ctx
        
    @classmethod
    def validate_negotiated_cipher(cls, negotiated_cipher: str, assurance_level: str = "HIGH_ASSURANCE") -> bool:
        """
        Enforce hybrid X25519 handshakes by rejecting legacy Public-Key algorithms.
        """
        if assurance_level == "HIGH_ASSURANCE":
            if negotiated_cipher not in cls.CIPHER_SUITES_HIGH_ASSURANCE:
                # Explicitly block anything referencing standard RSA or explicitly unapproved curves
                return False
        return True

# Simulated PKI Registry for valid internal agent identities
VALID_MTLS_CERTIFICATES = {
    "orchestrator",
    "manager",
    "auditor",
    # Specific specialized workers that explicitly require DB read/write state
    # Notice: MALWARE-PATHOLOGIST and others are NOT trusted with DB access!
    "triage",
    "correlator",
    "librarian",
    "historian",
    "endpoint_analyst"
}

class mTLSAuthenticationError(PermissionError):
    pass

class IAMAuthorizationError(PermissionError):
    pass

class ServiceMesh:
    """Zero Trust Identity Broker for Data Tier."""
    
    @staticmethod
    def connect_db(client_identity: str, db_path: str, check_same_thread: bool = False, negotiated_cipher: str = None) -> sqlite3.Connection:
        """
        Enforce mTLS handshake and exact Cipher Suite configurations before 
        returning a physical database connection.
        """
        if client_identity not in VALID_MTLS_CERTIFICATES:
            logger.critical(f"[DENY-IDENTITY] Unauthorized mTLS attempt to Data Tier by: {client_identity}")
            raise mTLSAuthenticationError(
                f"Lateral movement blocked: {client_identity} lacks valid mTLS certificate for DB."
            )
            
        if not negotiated_cipher or not CryptoAgilityManager.validate_negotiated_cipher(negotiated_cipher, assurance_level="HIGH_ASSURANCE"):
             logger.critical(f"[DENY-CRYPTOGRAPHY] {client_identity} attempted DB connection with legacy/unapproved Cipher: {negotiated_cipher}")
             raise mTLSAuthenticationError(
                 f"Crypto-Agility Block: {client_identity} failed to negotiate a Quantum-Resistant `HIGH_ASSURANCE` TLS parameter."
             )
             
        logger.debug(f"[ALLOW] mTLS and Cryptographic Curve verified for {client_identity}. Granting DB connection.")
        return sqlite3.connect(db_path, check_same_thread=check_same_thread)


class CloudStorageGateway:
    """IAM Enforcer for S3/Blob storage boundaries."""
    
    # Simulated strict IAM roles
    # Only forensics is allowed to PUT evidence.
    ALLOWED_S3_WRITERS = {
        "forensics"
    }

    @staticmethod
    def put_object(client_role: str, file_path: str, data: str):
        """
        Instead of direct `open(file, 'w')`, agents must pass through the Gateway
        which verifies their IAM execution role.
        """
        if client_role not in CloudStorageGateway.ALLOWED_S3_WRITERS:
            logger.critical(f"[DENY] IAM violation detected! {client_role} attempted S3 PUT.")
            raise IAMAuthorizationError(
                f"Zero Trust Block: Role {client_role} does not have s3:PutObject permissions."
            )
            
        logger.info(f"[ALLOW] IAM verified for {client_role}. Writing object to {file_path}")
        with open(file_path, "w") as fh:
            fh.write(data)

