"""watermarking_utils.py

Watermarking method utilities and registry.
"""

from __future__ import annotations

from typing import Dict, List

from watermarking_method import WatermarkingMethod

from add_after_eof import AddAfterEOF
from unsafe_bash_bridge_append_eof import UnsafeBashBridgeAppendEOF

print("🚀 Initializing watermarking methods registry...")

# Try to import QR method
try:
    from qr_watermarking_method import SimpleQRWatermarking
    QR_AVAILABLE = True
    print("✅ Successfully imported SimpleQRWatermarking")
except ImportError as e:
    QR_AVAILABLE = False
    print(f"❌ Failed to import SimpleQRWatermarking: {e}")

# --------------------
# Method registry
# --------------------

METHODS: Dict[str, WatermarkingMethod] = {
    "toy-eof": AddAfterEOF(),
    "bash-bridge-eof": UnsafeBashBridgeAppendEOF(),
}

# Add QR method if available
if QR_AVAILABLE:
    try:
        METHODS["simple-qr"] = SimpleQRWatermarking()
        print("✅ Successfully registered simple-qr method")
    except Exception as e:
        print(f"❌ Failed to register simple-qr method: {e}")
else:
    print("❌ QR method not available for registration")

print(f"📋 Final registered methods: {list(METHODS.keys())}")

def get_available_methods() -> List[str]:
    """Get list of available watermarking methods."""
    return list(METHODS.keys())

def get_method(name: str) -> WatermarkingMethod:
    """Get watermarking method by name."""
    if name not in METHODS:
        raise ValueError(f"Unknown watermarking method: {name}")
    return METHODS[name]

def get_method_description(name: str) -> str:
    """Get description for a watermarking method."""
    method = get_method(name)
    return method.get_usage()
