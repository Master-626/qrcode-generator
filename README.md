# QR Code Generator

## 简体中文摘要

这是一个小巧的二维码工具，可以从命令行或 Python 生成文本、网址和 Wi-Fi 的 PNG 图片，也支持按行批量生成。Wi-Fi 的名称、密码和加密方式会按常见扫描器的规则转义；隐藏网络加上 `--hidden`。默认不覆盖已有文件。需要 Python 3.11 或更高版本。安装：`pip install .`。示例：`qrgen generate -d "https://example.com" -o site.png`，`qrgen wifi --ssid MyWiFi --password secret --hidden -o wifi.png`。测试：`pip install -e ".[dev]" && pytest`。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

Generate PNG QR codes for text, URLs, and Wi-Fi networks. Use it as the `qrgen` command or as the `qrcode_generator` library. The tool writes a new image and leaves existing files alone. Wi-Fi payloads follow the `WIFI:` text format used by common phone scanners.

## Features

- Text and URL QR codes
- Wi-Fi QR codes, including hidden networks
- Batch generation from a UTF-8 text file, one payload per line
- Box size, border, and colors
- A small Python API

## Installation

Python 3.11 or newer is required. Current releases of Pillow and Click do not install on older Python versions.

```bash
git clone https://github.com/Master-626/qrcode-generator.git
cd qrcode-generator
pip install .
```

Editable install with test and lint tools:

```bash
pip install -e ".[dev]"
```

The commands `qrgen` and `qrcode-generator` are equivalent.

## Usage

```bash
# Text or URL
qrgen generate -d "Hello World" -o hello.png
qrgen generate -d "https://github.com/Master-626" -o github.png

# Wi-Fi. Quote values so the shell does not change them.
qrgen wifi --ssid "MyWiFi" --password "mypassword" -o wifi.png

# Hidden network (payload includes H:true)
qrgen wifi --ssid "MyWiFi" --password "mypassword" --hidden -o hidden.png

# Open network: pass an empty password
qrgen wifi --ssid "Guest" --password "" --security nopass -o open.png

# One QR code per line
qrgen batch -f urls.txt -o output_folder/
```

### Command options

`qrgen generate`

| Option | Default | Meaning |
| --- | --- | --- |
| `-d`, `--data` | required | Text to encode |
| `-o`, `--output` | `qrcode.png` | New PNG path |
| `--box-size` | `10` | Pixel size of each module. Must be greater than 0 |
| `--border` | `4` | Quiet-zone width in modules. Must be 0 or greater |

`qrgen wifi`

| Option | Default | Meaning |
| --- | --- | --- |
| `--ssid` | required | Network name. Must not be empty |
| `--password` | required | Pass `""` for an open network |
| `--security` | `WPA` | Literal security text, usually `WPA`, `WEP`, or `nopass` |
| `--hidden` | off | Add `H:true` for a hidden network |
| `-o`, `--output` | `wifi_qr.png` | New PNG path |

`qrgen batch`

| Option | Default | Meaning |
| --- | --- | --- |
| `-f`, `--file` | required | UTF-8 text file, one payload per line |
| `-o`, `--output-dir` | `qrcodes` | Directory to create. A filename prefix is not accepted here |

`qrgen --version` prints the installed package version. Failed commands exit with a nonzero status.

### Batch files

- Encode the file as UTF-8. A leading byte-order mark is ignored.
- Newlines (`\n`, `\r\n`, or `\r`) separate records and are not encoded.
- Spaces and tabs at the ends of a line are part of the payload.
- A blank line between other lines becomes a QR code of an empty string.
- Blank lines at the start or end of the file are ignored. An empty file, or a file made only of blank lines, creates the output directory and no images.
- The Python API does not apply these rules. `batch_generate` encodes each string you pass, exactly.

### Wi-Fi fields

Pass the SSID, password, and security text as literal characters, not as an already escaped `WIFI:` string. Backslashes, semicolons, commas, colons, and double quotes are escaped once. Quote shell arguments so the shell does not change them. No network is contacted.

With `hidden=False` (the default), the payload has no `H:` field:

```text
WIFI:T:WPA;S:MyWiFi;P:mypassword;;
```

`--hidden` inserts `H:true` before the closing semicolon:

```text
WIFI:T:WPA;S:MyWiFi;P:mypassword;H:true;;
```

## Python API

```python
from qrcode_generator import generate_qr, generate_wifi_qr, batch_generate

generate_qr("https://example.com", "output.png")
generate_qr(
    "https://example.com",
    "colored.png",
    box_size=8,
    border=2,
    fill_color="navy",
    back_color="white",
)

generate_wifi_qr("MyWiFi", "password123", output_path="wifi.png")
generate_wifi_qr("MyWiFi", "password123", hidden=True, output_path="hidden.png")
generate_wifi_qr("Guest", "", security="nopass", output_path="open.png")

batch_generate(["text1", "text2", "text3"], "output_dir")
batch_generate(["text1"], "output_dir", prefix="site")
```

`generate_qr` and `generate_wifi_qr` return a `pathlib.Path`. `batch_generate` returns a list of path strings. `data` may be `str` or `bytes`. `None` is rejected, because it would otherwise be encoded as the text `None`. `batch_generate` requires an iterable of strings; a single `str` or `bytes` object is rejected instead of encoding one image per character.

`prefix` is a filename prefix, not a path. It must be a string without `/`, `\`, `:`, or NUL. Empty prefixes, spaces, and non-ASCII prefixes are accepted. Choose the directory with `output_dir`.

Colors are selected with `fill_color` and `back_color` on `generate_qr`. The CLI generate command exposes box size and border; colors are available through the API.

## Output safety

Every generator creates a new PNG and refuses an existing file, directory, or symlink, including a dangling symlink. This replaces the old overwrite behavior. Pick a new output name, or remove the unwanted file yourself, before trying again.

If the output directory already exists and is not a directory, generation stops. That includes a regular file, a symlink to a file, and a dangling symlink. The existing entry is not replaced.

Iterable inputs are materialized once so every batch destination can be checked before the first image is written. A later error or race can leave earlier completed images. Batches are not all-or-nothing transactions.

Images are written in a private staging directory, then published with a no-replace hard link. The output filesystem must support hard links. A failure is reported rather than falling back to overwriting. A directory explicitly selected by the caller may itself be a symlink. This is not a sandbox against hostile replacement of the directory hierarchy.

## Testing

```bash
pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

Image decoding uses the optional `zxing-cpp` package. Without it, those cases are skipped rather than passed. Payload and output-safety tests still run. Tests use synthetic values only. Decoding an image does not show that a phone can join a real network.

```bash
pip install -e ".[dev,decode-test]"
pytest -rs
```

CI runs source and installed-wheel tests on Python 3.11, 3.12, and 3.13 across Linux, Windows, and macOS, then lints with Ruff. It also decodes generated PNGs with ZXing-C++ and checks the recovered fields with the unmodified ZXing Java 3.5.4 Wi-Fi parser, including both installed command aliases. Java 11 or newer is required for those semantic checks:

```bash
python validation/fetch_zxing.py
python validation/check_roundtrips.py --source src --output source-roundtrips.json
# After installing a built wheel:
python validation/check_roundtrips.py --aliases --output wheel-roundtrips.json
```

The Java dependency is downloaded from Maven Central and verified against a pinned SHA-256. Use UTF-8 subprocess output (`PYTHONUTF8=1`) on Windows. Test evidence is retained as workflow artifacts. CI does not publish package releases.

## License

MIT License
