"""
CLI interface for qrcode-generator.
"""

import click
from pathlib import Path

from .generator import generate_qr, generate_wifi_qr, batch_generate


@click.group()
@click.version_option()
def main():
    """QR Code Generator - Generate QR codes for text, URLs, and WiFi."""
    pass


@main.command()
@click.option("-d", "--data", required=True, help="Data to encode in QR code")
@click.option("-o", "--output", default="qrcode.png", help="Output image file")
@click.option("--box-size", type=int, default=10, help="QR code box size")
@click.option("--border", type=int, default=4, help="QR code border size")
def generate(data, output, box_size, border):
    """Generate a QR code from text or URL."""
    generate_qr(data, output, box_size=box_size, border=border)
    click.echo(f"✅ QR code saved to: {output}")


@main.command()
@click.option("--ssid", required=True, help="WiFi network name")
@click.option("--password", required=True, help="WiFi password")
@click.option("--security", default="WPA", help="Security type (WPA/WEP/nopass)")
@click.option("-o", "--output", default="wifi_qr.png", help="Output image file")
def wifi(ssid, password, security, output):
    """Generate a WiFi QR code."""
    generate_wifi_qr(ssid, password, security=security, output_path=output)
    click.echo(f"✅ WiFi QR code saved to: {output}")


@main.command()
@click.option("-f", "--file", required=True, help="Text file with one data per line")
@click.option("-o", "--output-dir", default="qrcodes", help="Output directory")
def batch(file, output_dir):
    """Batch generate QR codes from a text file."""
    data_list = Path(file).read_text(encoding="utf-8").strip().split("\n")
    generated = batch_generate(data_list, output_dir)
    click.echo(f"✅ Generated {len(generated)} QR codes in {output_dir}/")


if __name__ == "__main__":
    main()
