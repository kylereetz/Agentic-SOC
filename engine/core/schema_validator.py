"""
RCA Schema Validator: Validates asset records against the canonical JSON Schema.

Usage:
    from engine.core.schema_validator import validate_asset, assert_valid_asset

    asset = {"ip_address": "192.168.1.1", "mac_address": "aa:bb:cc:dd:ee:ff",
             "discovery_method": "active_arp"}
    if validate_asset(asset):
        print("Asset is valid")

# Satisfies NIST 800-171 Rev 3:
# 3.4.1 - Establish and maintain baseline configurations and inventories.
"""

import json
import logging
import os
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

_SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # engine/
    "schemas",
    "asset_schema.json",
)

# Load schema once at module import time
_SCHEMA: Dict[str, Any] = {}
try:
    with open(_SCHEMA_PATH, "r") as _fh:
        _SCHEMA = json.load(_fh)
except FileNotFoundError:
    logger.error(f"Asset schema not found at {_SCHEMA_PATH}")
except Exception as _exc:
    logger.error(f"Failed to load asset schema: {_exc}")


def _get_validator():
    """
    Lazily construct a jsonschema validator.
    Returns (validator_instance, None) on success, (None, error_message) on failure.
    """
    try:
        import jsonschema  # noqa: PLC0415
        validator = jsonschema.Draft7Validator(_SCHEMA)
        return validator, None
    except ImportError:
        msg = (
            "jsonschema is not installed. Asset validation disabled. "
            "Run: pip install jsonschema"
        )
        logger.warning(msg)
        return None, msg
    except Exception as exc:
        msg = f"Failed to initialise validator: {exc}"
        logger.error(msg)
        return None, msg


def validate_asset(asset: Dict[str, Any]) -> bool:
    """
    Validate an asset dict against the RCA canonical asset schema.

    Args:
        asset: Asset dictionary to validate.

    Returns:
        True if valid, False if invalid or if jsonschema is not installed.

    # Satisfies NIST 800-171 3.4.1
    """
    if not _SCHEMA:
        logger.warning("Asset schema not loaded — skipping validation.")
        return False

    validator, err = _get_validator()
    if validator is None:
        return False

    errors = list(validator.iter_errors(asset))
    if errors:
        for e in errors:
            logger.warning(f"Asset validation error: {e.message} (path: {list(e.path)})")
        return False

    return True


def assert_valid_asset(asset: Dict[str, Any]) -> None:
    """
    Like validate_asset() but raises ValueError on failure.
    Useful in ingest pipelines where invalid assets should stop processing.

    Args:
        asset: Asset dictionary to validate.

    Raises:
        ValueError: If the asset does not conform to the schema.
    """
    if not validate_asset(asset):
        raise ValueError(
            f"Asset record failed schema validation: {asset.get('ip_address', 'unknown IP')}"
        )


def get_validation_errors(asset: Dict[str, Any]) -> Tuple[bool, list]:
    """
    Return (is_valid, list_of_error_messages) for detailed diagnostics.

    Args:
        asset: Asset dictionary to validate.

    Returns:
        A tuple of (bool, list[str]).
    """
    if not _SCHEMA:
        return False, ["Asset schema not loaded"]

    validator, err = _get_validator()
    if validator is None:
        return False, [err or "Validator unavailable"]

    import jsonschema  # noqa: PLC0415
    errors = [e.message for e in validator.iter_errors(asset)]
    return (len(errors) == 0), errors
