"""Hidden Wi-Fi networks add H:true and leave the default payload unchanged."""

import pytest
from click.testing import CliRunner
from PIL import Image

from qrcode_generator import generate_wifi_qr
from qrcode_generator.cli import main
from tests.test_wifi_payload import CASES, expected_payload


def _record(monkeypatch):
    seen = []

    def record(data, output):
        seen.append((data, output))
        return output

    monkeypatch.setattr("qrcode_generator.generator.generate_qr", record)
    return seen


@pytest.mark.parametrize(("ssid", "password", "security"), CASES)
@pytest.mark.parametrize("hidden", [False, True])
def test_hidden_flag_only_adds_h_true(monkeypatch, ssid, password, security, hidden):
    seen = _record(monkeypatch)
    generate_wifi_qr(ssid, password, security, "unused.png", hidden=hidden)
    base = expected_payload(ssid, password, security)
    payload = base[:-1] + "H:true;;" if hidden else base
    assert seen == [(payload, "unused.png")]
    if not hidden:
        assert "H:" not in payload
    else:
        assert payload.endswith(";H:true;;")


def test_hidden_rejects_non_bool_before_writing(tmp_path):
    output = tmp_path / "wifi.png"
    with pytest.raises(TypeError, match="hidden"):
        generate_wifi_qr("Cafe", "secret", hidden=1, output_path=output)
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_empty_ssid_is_rejected_before_writing(tmp_path):
    output = tmp_path / "nested" / "wifi.png"
    with pytest.raises(ValueError, match="SSID"):
        generate_wifi_qr("", "secret", output_path=output)
    assert not output.parent.exists()


@pytest.mark.parametrize("value", [None, 5, b"Cafe"])
def test_wifi_fields_must_be_strings(tmp_path, value):
    output = tmp_path / "wifi.png"
    with pytest.raises(TypeError):
        generate_wifi_qr(value, "secret", output_path=output)
    with pytest.raises(TypeError):
        generate_wifi_qr("Cafe", value, output_path=output)
    assert not output.exists()


def test_cli_empty_ssid_is_an_error(tmp_path):
    output = tmp_path / "wifi.png"
    result = CliRunner().invoke(
        main,
        ["wifi", "--ssid", "", "--password", "secret", "-o", str(output)],
    )
    assert result.exit_code != 0
    assert "SSID" in result.output
    assert "saved" not in result.output
    assert not output.exists()


def _decode(path):
    decoder = pytest.importorskip("zxingcpp", reason="install .[decode-test]")
    with Image.open(path) as image:
        pixels = image.convert("L")
        decoded = decoder.read_barcode(
            memoryview(pixels.tobytes()).cast("B", shape=(pixels.height, pixels.width))
        )
    assert decoded is not None
    return decoded.bytes


@pytest.mark.parametrize("route", ["api", "cli"])
def test_hidden_image_round_trip(tmp_path, route):
    output = tmp_path / "wifi.png"
    ssid, password, security = "Cafe;Guest", "p:a\\ss", "WPA"
    expected = expected_payload(ssid, password, security)[:-1] + "H:true;;"
    if route == "api":
        assert generate_wifi_qr(ssid, password, security, output, hidden=True) == output
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
                "--hidden",
                "-o",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
    assert _decode(output) == expected.encode("utf-8")


def test_default_cli_wifi_omits_hidden_field(tmp_path):
    output = tmp_path / "wifi.png"
    result = CliRunner().invoke(
        main,
        [
            "wifi",
            "--ssid",
            "Open",
            "--password",
            "",
            "--security",
            "nopass",
            "-o",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assert _decode(output) == b"WIFI:T:nopass;S:Open;P:;;"
