"""
qrcode-generator - QR code generator with batch support.
"""

from .generator import batch_generate, generate_qr, generate_wifi_qr

__version__ = "0.1.1"
__all__ = ["generate_qr", "generate_wifi_qr", "batch_generate"]
