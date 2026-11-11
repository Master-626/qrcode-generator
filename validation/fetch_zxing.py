"""Fetch a checksum-pinned Maven Central artifact for semantic Wi-Fi tests."""

import hashlib
from pathlib import Path
from urllib.request import urlopen

URL = "https://repo.maven.apache.org/maven2/com/google/zxing/core/3.5.4/core-3.5.4.jar"
SHA256 = "71de5d89341b5fcf5dd89da7f44e84d825d0e084cdf3ec77c9abe26b0f0ceb13"


def main():
    with urlopen(URL, timeout=60) as response:
        data = response.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != SHA256:
        raise ValueError("ZXing artifact checksum mismatch: " + actual)
    destination = Path(__file__).resolve().parent / "core-3.5.4.jar"
    destination.write_bytes(data)
    print("Verified ZXing core 3.5.4: " + actual)


if __name__ == "__main__":
    main()
