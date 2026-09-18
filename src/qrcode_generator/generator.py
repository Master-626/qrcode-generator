"""
Core QR code generation logic.
"""

import qrcode
from pathlib import Path
from typing import List


def generate_qr(
    data: str,
    output_path: str,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white",
):
    """Generate a QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_p)

    return output_p


def generate_wifi_qr(
    ssid: str,
    password: str,
    security: str = "WPA",
    output_path: str = "wifi_qr.png",
):
    """Generate a WiFi QR code."""
    wifi_data = f"WIFI:T:{security};S:{ssid};P:{password};;"
    return generate_qr(wifi_data, output_path)


def batch_generate(
    data_list: List[str],
    output_dir: str,
    prefix: str = "qr",
):
    """Batch generate QR codes."""
    output_p = Path(output_dir)
    output_p.mkdir(parents=True, exist_ok=True)

    generated = []
    for i, data in enumerate(data_list):
        output_file = output_p / f"{prefix}_{i+1}.png"
        generate_qr(data, str(output_file))
        generated.append(str(output_file))

    return generated
