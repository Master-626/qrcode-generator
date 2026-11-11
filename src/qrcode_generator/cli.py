"""
CLI interface for qrcode-generator.
"""

from pathlib import Path

import click
from qrcode.exceptions import DataOverflowError

from .generator import batch_generate, generate_qr, generate_wifi_qr


def read_batch_lines(text):
    """Split batch text into payloads without changing line contents.

    ``\\n``, ``\\r\\n`` and ``\\r`` are separators, not data. Spaces stay on
    the line. Leading and trailing blank lines are ignored, and an empty file
    produces no payloads. A blank line between other lines is kept.
    """
    lines = text.splitlines()
    start = 0
    end = len(lines)
    while start < end and lines[start] == "":
        start += 1
    while end > start and lines[end - 1] == "":
        end -= 1
    return lines[start:end]


def load_batch_file(path):
    """Read a UTF-8 batch file. A leading byte-order mark is ignored."""
    return read_batch_lines(Path(path).read_text(encoding="utf-8-sig"))


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
    try:
        generate_qr(data, output, box_size=box_size, border=border)
    except (OSError, ValueError, DataOverflowError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"✅ QR code saved to: {output}")


@main.command()
@click.option("--ssid", required=True, help="WiFi network name")
@click.option("--password", required=True, help="WiFi password")
@click.option("--security", default="WPA", help="Security type (WPA/WEP/nopass)")
@click.option(
    "--hidden",
    is_flag=True,
    help="Mark the network as hidden (adds H:true to the payload)",
)
@click.option("-o", "--output", default="wifi_qr.png", help="Output image file")
def wifi(ssid, password, security, hidden, output):
    """Generate a WiFi QR code."""
    try:
        generate_wifi_qr(
            ssid,
            password,
            security=security,
            output_path=output,
            hidden=hidden,
        )
    except (OSError, ValueError, DataOverflowError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"✅ WiFi QR code saved to: {output}")


@main.command()
@click.option("-f", "--file", required=True, help="Text file with one data per line")
@click.option("-o", "--output-dir", default="qrcodes", help="Output directory")
def batch(file, output_dir):
    """Batch generate QR codes from a text file."""
    try:
        data_list = load_batch_file(file)
        generated = batch_generate(data_list, output_dir)
    except (OSError, ValueError, DataOverflowError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"✅ Generated {len(generated)} QR codes in {output_dir}/")


if __name__ == "__main__":
    main()
