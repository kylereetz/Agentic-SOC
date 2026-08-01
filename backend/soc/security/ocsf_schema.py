"""
Open Cybersecurity Schema Framework (OCSF) Normalization Module.
Maps disparate security log events to standardized OCSF event classes.
"""

from enum import IntEnum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class OCSFClassUID(IntEnum):
    AUTHENTICATION = 3002
    NETWORK_ACTIVITY = 4001
    PROPRIETARY_OT = 9999


class OCSFMetadata(BaseModel):
    version: str = "1.0-OCSF"
    normalization_type: str = "standard"  # "standard" or "custom_OT_inferred"


class OCSFEndpoint(BaseModel):
    ip: str
    port: Optional[int] = None


class OCSFEventBase(BaseModel):
    """The base OCSF shape that all derived events must adhere to."""

    metadata: OCSFMetadata
    ocsf_class_uid: int
    time: float
    src_endpoint: Optional[OCSFEndpoint] = None
    dst_endpoint: Optional[OCSFEndpoint] = None
    unmapped: Dict[str, Any] = Field(default_factory=dict)


class OCSFAuthentication(OCSFEventBase):
    """OCSF Class 3002: Authentication"""

    ocsf_class_uid: int = OCSFClassUID.AUTHENTICATION.value
    user: Optional[str] = None
    status: str = "Unknown"  # Success, Failure, etc.
    message: str = ""


class OCSFNetworkActivity(OCSFEventBase):
    """OCSF Class 4001: Network Activity"""

    ocsf_class_uid: int = OCSFClassUID.NETWORK_ACTIVITY.value
    protocol: str = "Unknown"
    action: str = "Unknown"  # Allowed, Denied, etc.
    bytes_in: int = 0
    bytes_out: int = 0


class OCSFProprietaryOT(OCSFEventBase):
    """Extension profile for legacy factory devices where `unmapped` holds context."""

    ocsf_class_uid: int = OCSFClassUID.PROPRIETARY_OT.value
    message: str = ""
    # The 'unmapped' dict from the base class will carry the heavy lifting here.
