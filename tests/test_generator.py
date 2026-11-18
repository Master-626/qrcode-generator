from qrcode_generator.generator import generate_qr, generate_wifi_qr


def test_generate_qr(tmp_path):
    """Test QR code generation."""
    output = tmp_path / "test.png"
    generate_qr("https://example.com", str(output))
    assert output.exists()
    assert output.stat().st_size > 0


def test_generate_wifi_qr(tmp_path):
    """Test WiFi QR code generation."""
    output = tmp_path / "wifi.png"
    generate_wifi_qr("MyWiFi", "mypassword123", output_path=str(output))
    assert output.exists()
    assert output.stat().st_size > 0
