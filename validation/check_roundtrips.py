"""Decode actual PNGs with ZXing-C++; parse using unmodified ZXing Java 3.5.4."""

import argparse
import base64
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import zxingcpp
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--source")
    parser.add_argument("--aliases", action="store_true")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    if args.source:
        sys.path.insert(0, args.source)
        os.environ["PYTHONPATH"] = args.source
    from qrcode_generator import generate_wifi_qr

    spec = importlib.util.spec_from_file_location(
        "cases", here.parent / "tests/test_wifi_payload.py"
    )
    cases = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cases)
    routes = ["api", "module"]
    if args.aliases:
        routes += ["qrgen", "qrcode-generator"]
    entries = []
    with tempfile.TemporaryDirectory(prefix="qr-roundtrip-") as directory:
        for route in routes:
            for index, (ssid, password, security) in enumerate(cases.CASES):
                output = Path(directory) / (route + "-" + str(index) + ".png")
                if route == "api":
                    generate_wifi_qr(ssid, password, security, output)
                else:
                    command = (
                        [sys.executable, "-m", "qrcode_generator.cli"]
                        if route == "module"
                        else [shutil.which(route) or route]
                    )
                    subprocess.run(
                        command
                        + [
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
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                with Image.open(output) as image:
                    pixels = image.convert("L")
                    decoded = zxingcpp.read_barcode(
                        memoryview(pixels.tobytes()).cast(
                            "B", shape=(pixels.height, pixels.width)
                        )
                    )
                assert decoded is not None, (route, index)
                entries.append(
                    {
                        "route": route,
                        "case": index,
                        "expected": [
                            ssid,
                            password or None,
                            security,
                            "false",
                            None,
                            None,
                            None,
                            None,
                        ],
                        "decoded_payload": decoded.bytes.decode("utf-8"),
                    }
                )
    java_input = (
        "\n".join(
            base64.b64encode(e["decoded_payload"].encode("utf-8")).decode("ascii")
            for e in entries
        )
        + "\n"
    )
    result = subprocess.run(
        [
            "java",
            "--class-path",
            str(here / "core-3.5.4.jar"),
            str(here / "ParseWifi.java"),
        ],
        input=java_input,
        text=True,
        capture_output=True,
        check=True,
    )
    lines = result.stdout.splitlines()
    assert len(lines) == len(entries), result.stdout
    for entry, line in zip(entries, lines):
        if line == "INVALID":
            parsed = None
        else:
            parts = line.split("\t")
            parsed = [
                value
                if i == 3
                else None
                if value == "-"
                else base64.b64decode(value).decode("utf-8")
                for i, value in enumerate(parts)
            ]
        entry["parsed"] = parsed
        entry["passed"] = parsed == entry["expected"]
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source": args.source or "installed wheel",
        "dependencies": {
            package: importlib.metadata.version(package)
            for package in ("qrcode", "Pillow", "click", "zxing-cpp")
        },
        "java_parser": "com.google.zxing:core:3.5.4 WifiResultParser (unmodified)",
        "passed": sum(e["passed"] for e in entries),
        "total": len(entries),
        "entries": entries,
    }
    Path(args.output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("{passed}/{total} exact image/parser round trips passed".format(**report))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
