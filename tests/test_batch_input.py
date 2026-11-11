"""Batch-file parsing and the payloads those lines encode."""

import pytest
from click.testing import CliRunner
from PIL import Image

from qrcode_generator import batch_generate, generate_qr
from qrcode_generator.cli import load_batch_file, main, read_batch_lines


def test_read_batch_lines_keeps_spaces_and_blank_rows():
    text = "\n  hello  \n\nworld \n\n"
    assert read_batch_lines(text) == ["  hello  ", "", "world "]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", []),
        ("\n", []),
        ("\r\n", []),
        ("\n\n", []),
        ("a\n", ["a"]),
        ("a\r\nb\r\n", ["a", "b"]),
        ("only\r", ["only"]),
        ("a\n\nb", ["a", "", "b"]),
        ("\nhello\n", ["hello"]),
        ("   \n", ["   "]),
        ("\thello\t\n", ["\thello\t"]),
        ("  first  \n  last  ", ["  first  ", "  last  "]),
        ("café \r\n雪\r\n", ["café ", "雪"]),
    ],
)
def test_read_batch_lines_edge_cases(text, expected):
    assert read_batch_lines(text) == expected


def test_load_batch_file_ignores_bom_and_crlf(tmp_path):
    path = tmp_path / "urls.txt"
    path.write_bytes(
        "\ufeff  https://example.com/a  \r\n\r\nhttps://example.com/b \r\n".encode()
    )
    assert load_batch_file(path) == [
        "  https://example.com/a  ",
        "",
        "https://example.com/b ",
    ]


def test_cli_batch_passes_literal_lines(tmp_path, monkeypatch):
    captured = {}

    def record(data_list, output_dir, prefix="qr"):
        captured["data"] = list(data_list)
        captured["output"] = output_dir
        captured["prefix"] = prefix
        return []

    monkeypatch.setattr("qrcode_generator.cli.batch_generate", record)
    source = tmp_path / "input.txt"
    source.write_bytes(b"\xef\xbb\xbf hello\r\n\r\nworld \r\n")
    output = tmp_path / "images"
    result = CliRunner().invoke(main, ["batch", "-f", str(source), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert captured == {
        "data": [" hello", "", "world "],
        "output": str(output),
        "prefix": "qr",
    }


def test_cli_empty_batch_file_creates_no_images(tmp_path):
    source = tmp_path / "empty.txt"
    source.write_bytes(b"")
    output = tmp_path / "images"
    result = CliRunner().invoke(main, ["batch", "-f", str(source), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert "Generated 0 QR codes" in result.output
    assert output.is_dir()
    assert list(output.iterdir()) == []


def test_cli_newline_only_file_creates_no_images(tmp_path):
    source = tmp_path / "blank.txt"
    source.write_bytes(b"\r\n")
    output = tmp_path / "images"
    result = CliRunner().invoke(main, ["batch", "-f", str(source), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert list(output.iterdir()) == []


def test_cli_batch_directory_input_is_an_error(tmp_path):
    result = CliRunner().invoke(
        main, ["batch", "-f", str(tmp_path), "-o", str(tmp_path / "out")]
    )
    assert result.exit_code != 0
    assert "Error:" in result.output
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("value", ["ab", b"ab", bytearray(b"ab")])
def test_batch_rejects_a_single_string_or_bytes(tmp_path, value):
    output = tmp_path / "images"
    with pytest.raises(TypeError, match="data_list"):
        batch_generate(value, output)
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_none_data_does_not_encode_the_word_none(tmp_path):
    output = tmp_path / "missing" / "out.png"
    with pytest.raises(TypeError, match="not None"):
        generate_qr(None, output)
    assert not output.parent.exists()


@pytest.mark.parametrize(("box_size", "border"), [(0, 4), (-2, 4), (10, -1)])
def test_invalid_geometry_writes_nothing(tmp_path, box_size, border):
    output = tmp_path / "out.png"
    with pytest.raises(ValueError):
        generate_qr("payload", output, box_size=box_size, border=border)
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


def test_batch_images_round_trip_literal_lines(tmp_path):
    source = tmp_path / "input.txt"
    lines = ["  https://example.com/a  ", "", "café "]
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output = tmp_path / "images"
    result = CliRunner().invoke(main, ["batch", "-f", str(source), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert _decode(output / "qr_1.png") == lines[0].encode("utf-8")
    assert _decode(output / "qr_3.png") == lines[2].encode("utf-8")
    # An empty payload is a valid PNG, but scanners do not return it as text.
    with Image.open(output / "qr_2.png") as image:
        assert image.format == "PNG"
        image.verify()


def test_text_qr_round_trip_past_version_one(tmp_path):
    payload = "https://example.com/" + ("snow-雪-" * 40)
    output = tmp_path / "long.png"
    assert generate_qr(payload, output) == output
    assert _decode(output) == payload.encode("utf-8")


def test_bytes_payload_round_trip(tmp_path):
    output = tmp_path / "bytes.png"
    assert generate_qr(b"hello", output) == output
    assert _decode(output) == b"hello"


def test_cli_empty_string_writes_png(tmp_path):
    output = tmp_path / "empty.png"
    result = CliRunner().invoke(main, ["generate", "-d", "", "-o", str(output)])
    assert result.exit_code == 0, result.output
    with Image.open(output) as image:
        assert image.format == "PNG"
        image.verify()
