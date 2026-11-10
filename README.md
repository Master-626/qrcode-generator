# QR Code Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

A QR code generator with batch support and WiFi QR code generation.

## 🌟 Features

- 📱 **Text/URL QR** - Generate QR codes from any text or URL
- 📶 **WiFi QR** - Generate WiFi QR codes for easy sharing
- 📦 **Batch Mode** - Generate multiple QR codes from a text file
- 🎨 **Customizable** - Control box size, border, colors
- 🐍 **Python API** - Use as a library in your code

## 📦 Installation

```bash
git clone https://github.com/Master-626/qrcode-generator.git
cd qrcode-generator
pip install .
```

## 🚀 Usage

### Generate QR Code
```bash
# Basic text QR code
qrgen generate -d "Hello World" -o hello.png

# URL QR code
qrgen generate -d "https://github.com/Master-626" -o github.png
```

### WiFi QR Code
```bash
qrgen wifi --ssid "MyWiFi" --password "mypassword" -o wifi.png
```

### Batch Generate
```bash
# Generate from a file (one QR per line)
qrgen batch -f urls.txt -o output_folder/
```

## 🐍 Python API

```python
from qrcode_generator import generate_qr, generate_wifi_qr, batch_generate

# Generate basic QR
generate_qr("https://example.com", "output.png")

# Generate WiFi QR
generate_wifi_qr("MyWiFi", "password123", output_path="wifi.png")

# Batch generate
batch_generate(["text1", "text2", "text3"], "output_dir")
```

### WiFi field input

Supply literal SSID/password/security text, not pre-escaped WiFi payload text.
Backslashes, semicolons, commas, colons and double quotes are escaped once in
the QR payload. Quote shell arguments appropriately so your shell does not
change the values before this program receives them. No network is contacted.

### Output safety and compatibility

All generators create new PNG files and refuse existing files, directories and
filename symlinks (including dangling links). This intentionally replaces the
old overwrite behavior. Choose a new output name or remove an unwanted file
yourself before trying again. CLI errors return a nonzero exit status.

The batch API's `prefix` is a filename prefix, not a path. It must be a string
without `/`, `\\`, `:`, or NUL; empty, Unicode and space-containing prefixes are
accepted. Use `output_dir` to select the directory. Every batch destination is
checked before writing any images. Iterable inputs are materialized once for
this preflight. A later error or race can leave earlier completed images;
batches are not all-or-nothing transactions.

Images are written to private staging directories, then published with a
no-replace hard link. The output filesystem must support hard links. A failure
is reported rather than falling back to overwriting. A directory explicitly
selected by the caller may itself be a symlink. This is not a sandbox against
hostile replacement of the directory hierarchy. The CI workflow tests native
Linux, Windows and macOS runners; other filesystems and phone scanners need
separate validation.

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest
```

For independent image-decoding tests, install the additional test dependency:

```bash
pip install -e ".[dev,decode-test]"
pytest -rs
```

Without `decode-test`, 36 image-decoding cases are skipped, not passed. The
remaining payload and output-safety tests still run. Tests use synthetic values
only; image decoding does not establish that a phone can join a real network.

CI runs source and installed-wheel tests on Python 3.8 and 3.13 across Linux,
Windows and macOS. It also decodes generated PNGs with ZXing-C++ and checks the
recovered fields with the unmodified ZXing Java 3.5.4 Wi-Fi parser, including
both installed command aliases. Java 11+ is required for these semantic checks:

```bash
python validation/fetch_zxing.py
python validation/check_roundtrips.py --source src --output source-roundtrips.json
# After installing a built wheel:
python validation/check_roundtrips.py --aliases --output wheel-roundtrips.json
```

The Java dependency is downloaded from Maven Central and verified against a
pinned SHA-256. Use UTF-8 subprocess output (`PYTHONUTF8=1`) on Windows. Test
evidence is retained as workflow artifacts; CI does not publish package releases.

## 📄 License

MIT License
