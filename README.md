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

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest
```

## 📄 License

MIT License
