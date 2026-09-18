"""
qrcode-generator - QR code generator with batch support.
"""

from .generator import generate_qr, generate_wifi_qr, batch_generate

__version__ = "0.1.0"
__all__ = ["generate_qr", "generate_wifi_qr", "batch_generate"]
