"""Synthetic credentials only. ZXing-C++ decodes actual generated image pixels."""

import pytest
from click.testing import CliRunner
from PIL import Image

from qrcode_generator import generate_wifi_qr
from qrcode_generator.cli import main

CASES = [
    ("MyWiFi", "password123", "WPA"),
    ("Cafe;Guest", "semi;colon", "WPA"),
    (r"Cafe\Guest", r"back\slash", "WPA"),
    (r"Cafe\;Guest", r"literal\;password", "WPA"),
    ("Guest;P:spoof", "actual-password", "WPA"),
    ("Guest;H:true", "actual-password", "WPA"),
    ("Guest", "value;H:true;S:spoof", "WPA"),
    ("Colon:Guest", "colon:password", "WPA"),
    ("Comma,Guest", "comma,password", "WPA"),
    ('Quote"Guest', 'quote"password', "WPA"),
    ("trailing\\", "password\\", "WPA"),
    ("double\\\\", "password\\\\", "WPA"),
    (" 雪 café ", " 密码 café ", "WPA"),
    (" leading trailing ", " password ", "WEP"),
    ("Open", "", "nopass"),
    ("Guest", "password", 'WPA;S:spoof\\,"'),
    ('All\\;,:"', 'All\\;,:"', "WPA"),
    ("Line\nBreak", "tabs\tinside", "WPA"),
]


def expected_payload(ssid, password, security):
    # Deliberately different construction from production's per-character loop.
    def escape(value):
        value = value.replace("\\", "\\\\")
        for reserved in (";", ",", ":", '"'):
            value = value.replace(reserved, "\\" + reserved)
        return value

    return "WIFI:T:{};S:{};P:{};;".format(
        escape(security), escape(ssid), escape(password)
    )


@pytest.mark.parametrize("ssid,password,security", CASES)
@pytest.mark.parametrize("route", ["api", "cli"])
def test_wifi_image_decodes_literal_fields(tmp_path, ssid, password, security, route):
    decoder = pytest.importorskip("zxingcpp", reason="install .[decode-test]")
    output = tmp_path / "wifi.png"
    if route == "api":
        assert generate_wifi_qr(ssid, password, security, output) == output
    else:
        result = CliRunner().invoke(
            main,
            [
                "wifi",
                "--ssid",
                ssid,
                "--password",
                password,
                "--security",
                security,
                "-o",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
    with Image.open(output) as image:
        pixels = image.convert("L")
        decoded = decoder.read_barcode(
            memoryview(pixels.tobytes()).cast("B", shape=(pixels.height, pixels.width))
        )
    assert decoded is not None
    assert decoded.bytes == expected_payload(ssid, password, security).encode("utf-8")


@pytest.mark.parametrize("ssid,password,security", CASES)
def test_literal_fields_without_decoder(monkeypatch, ssid, password, security):
    import qrcode_generator.generator as generator

    seen = []
    monkeypatch.setattr(
        generator, "generate_qr", lambda data, output: seen.append((data, output))
    )
    generator.generate_wifi_qr(ssid, password, security, "unused.png")
    assert seen == [(expected_payload(ssid, password, security), "unused.png")]
