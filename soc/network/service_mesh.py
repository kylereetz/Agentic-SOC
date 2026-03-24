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

logger = logging.getLogger("RCA-ServiceMesh")

# Simulated PKI Registry for valid internal agent identities
VALID_MTLS_CERTIFICATES = {
    "orchestrator",
    "manager",
    "auditor",
    # Specific specialized workers that explicitly require DB read/write state
    # Notice: MALWARE-PATHOLOGIST and others are NOT trusted with DB access!
    "triage",
    "correlator"
}

class mTLSAuthenticationError(PermissionError):
    pass

class IAMAuthorizationError(PermissionError):
    pass

class ServiceMesh:
    """Zero Trust Identity Broker for Data Tier."""
    
    @staticmethod
    def connect_db(client_identity: str, db_path: str, check_same_thread: bool = False) -> sqlite3.Connection:
        """
        Enforce mTLS handshake before returning a database connection.
        If the client_identity lacks a valid internal cert, block the connection.
        """
        if client_identity not in VALID_MTLS_CERTIFICATES:
            logger.critical(f"[DENY] Unauthorized mTLS attempt to Data Tier by: {client_identity}")
            raise mTLSAuthenticationError(
                f"Lateral movement blocked: {client_identity} lacks valid mTLS certificate for DB."
            )
            
        logger.debug(f"[ALLOW] mTLS verified for {client_identity}. Granting DB connection.")
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

