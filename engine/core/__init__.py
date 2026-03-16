"""
RCA Engine — Public API Surface.

Import classes directly from submodules for normal use, or use this
package for its __all__ listing. Lazy imports prevent collection failures
when optional heavy dependencies (scapy, nmap) are not yet installed.

    from engine.core.sentinel import SentinelEngine
    from engine.core.mapper import NISTMapper
    from engine.core.portscanner import PortScanner
    from engine.core.detector import run_local_hardening
    from engine.core.schema_validator import validate_asset
"""

__all__ = [
    "SentinelEngine",
    "NISTMapper",
    "IndustrialScanner",
    "PortScanner",
    "run_local_hardening",
    "validate_asset",
]


def __getattr__(name: str):
    """Lazy attribute loader — only import submodules when accessed."""
    _map = {
        "SentinelEngine": ("engine.core.sentinel", "SentinelEngine"),
        "NISTMapper": ("engine.core.mapper", "NISTMapper"),
        "IndustrialScanner": ("engine.core.industrial", "IndustrialScanner"),
        "PortScanner": ("engine.core.portscanner", "PortScanner"),
        "run_local_hardening": ("engine.core.detector", "run_local_hardening"),
        "validate_asset": ("engine.core.schema_validator", "validate_asset"),
    }
    if name in _map:
        import importlib
        module_path, attr = _map[name]
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module 'engine.core' has no attribute {name!r}")
