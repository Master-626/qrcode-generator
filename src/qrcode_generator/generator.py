"""
Core QR code generation logic.
"""

import errno
import os
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory

import qrcode


def _require_new_output(path: Path):
    """Reject any existing directory entry, including dangling symlinks."""
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise FileExistsError(errno.EEXIST, "Output already exists", str(path))


def _reject_non_directory(directory: Path):
    """Fail if this path exists and is not a directory.

    A symlink to a directory is allowed. A file, a symlink to a file, and a
    dangling symlink are left untouched. Missing paths are allowed so the
    caller can create them.
    """
    try:
        directory.lstat()
    except FileNotFoundError:
        return
    if directory.is_dir():
        return
    raise NotADirectoryError(
        errno.ENOTDIR, "Output directory is not a directory", str(directory)
    )


def _ensure_output_directory(directory: Path):
    """Create a directory without replacing a file or dangling symlink."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        # exist_ok only swallows the error when the path is already a directory.
        raise NotADirectoryError(
            errno.ENOTDIR, "Output directory is not a directory", str(directory)
        ) from None


def _escape_wifi_field(value: str) -> str:
    """Escape literal Wi-Fi field text once, without interpreting input escapes."""
    return "".join("\\" + char if char in '\\;,:"' else char for char in value)


def generate_qr(
    data: str,
    output_path: str,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white",
):
    """Generate a new PNG image; never replace an existing output entry."""
    if data is None:
        # qrcode would otherwise encode the text "None".
        raise TypeError("data must be a string or bytes, not None")
    output_p = Path(output_path)
    _reject_non_directory(output_p.parent)
    _require_new_output(output_p)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    _ensure_output_directory(output_p.parent)
    # A complete image becomes visible only if the destination is still absent.
    # Do not fall back to replacement on filesystems without hard-link support.
    with TemporaryDirectory(prefix=".qrgen-", dir=str(output_p.parent)) as staging:
        staged = Path(staging) / "image.png"
        img.save(staged, format="PNG")
        os.link(staged, output_p)

    return output_p


def generate_wifi_qr(
    ssid: str,
    password: str,
    security: str = "WPA",
    output_path: str = "wifi_qr.png",
    hidden: bool = False,
):
    """Generate a WiFi QR code from literal (not pre-escaped) field values.

    ``hidden=True`` appends the standard ``H:true`` field. The default payload
    is unchanged and does not include an ``H:`` field.
    """
    for name, value in (("ssid", ssid), ("password", password), ("security", security)):
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string")
    if ssid == "":
        raise ValueError("SSID must not be empty")
    if not isinstance(hidden, bool):
        raise TypeError("hidden must be a bool")
    wifi_data = (
        f"WIFI:T:{_escape_wifi_field(security)};"
        f"S:{_escape_wifi_field(ssid)};P:{_escape_wifi_field(password)};"
    )
    if hidden:
        wifi_data += "H:true;"
    wifi_data += ";"
    return generate_qr(wifi_data, output_path)


def batch_generate(
    data_list: Iterable[str],
    output_dir: str,
    prefix: str = "qr",
):
    """Generate new images using a filename-only prefix, with conflict preflight."""
    if not isinstance(prefix, str):
        raise TypeError("prefix must be a string")
    if any(char in prefix for char in ("/", "\\", ":", "\0")):
        raise ValueError(
            "prefix must be a filename prefix, without path separators, colon or NUL"
        )
    if isinstance(data_list, (str, bytes, bytearray)):
        raise TypeError(
            "data_list must be an iterable of strings, not a single string or bytes"
        )

    output_p = Path(output_dir)
    _reject_non_directory(output_p)
    # Materialize once so generators remain supported and every destination can
    # be checked before the first image is written. Later failures may leave
    # earlier completed images; batches are not all-or-nothing transactions.
    data_list = list(data_list)
    outputs = [output_p / f"{prefix}_{i + 1}.png" for i in range(len(data_list))]
    for output_file in outputs:
        _require_new_output(output_file)
    _ensure_output_directory(output_p)

    generated = []
    for data, output_file in zip(data_list, outputs):
        generate_qr(data, str(output_file))
        generated.append(str(output_file))

    return generated
