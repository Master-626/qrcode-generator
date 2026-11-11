import errno
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from qrcode_generator import batch_generate, generate_qr, generate_wifi_qr
from qrcode_generator.cli import main


def make_existing(path, kind):
    target = path.parent / "referent.txt"
    if kind == "file":
        path.write_bytes(b"existing")
    elif kind == "directory":
        path.mkdir()
    else:
        if kind == "symlink":
            target.write_bytes(b"referent")
        path.symlink_to(target)
    return target


def assert_existing(path, target, kind):
    if kind == "file":
        assert path.read_bytes() == b"existing"
    elif kind == "directory":
        assert path.is_dir()
        assert not list(path.iterdir())
    else:
        assert path.is_symlink()
        if kind == "symlink":
            assert target.read_bytes() == b"referent"
        else:
            assert not target.exists()


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "dangling"])
@pytest.mark.parametrize("route", ["text", "wifi", "batch"])
def test_existing_outputs_are_untouched(tmp_path, kind, route):
    path = tmp_path / ("qr_1.png" if route == "batch" else "output.png")
    target = make_existing(path, kind)
    with pytest.raises(FileExistsError):
        if route == "text":
            generate_qr("new", path)
        elif route == "wifi":
            generate_wifi_qr("Synthetic", "not-a-secret", output_path=path)
        else:
            batch_generate(["new"], tmp_path)
    assert_existing(path, target, kind)
    assert not list(tmp_path.glob(".qrgen-*"))


@pytest.mark.parametrize(
    "prefix",
    [
        "../outside",
        "/absolute",
        "part/name",
        r"..\outside",
        r"C:\outside",
        r"\\server\share",
        "C:drive",
        "nul\0",
    ],
)
def test_prefix_paths_rejected_without_output(tmp_path, prefix):
    if prefix == "/absolute":
        prefix = str(tmp_path / "absolute")
    output = tmp_path / "not-created"
    with pytest.raises(ValueError):
        batch_generate(["new"], output, prefix)
    assert not output.exists()
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("prefix", [None, 1, True, Path("prefix"), b"bytes"])
def test_prefix_must_be_string(tmp_path, prefix):
    with pytest.raises(TypeError):
        batch_generate(["new"], tmp_path / "new", prefix)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "prefix", ["qr", "", "..", " spaces ", "雪", ".hidden", "dots.and-dashes"]
)
def test_filename_prefixes_and_iterables_supported(tmp_path, prefix):
    output = tmp_path / "images"
    paths = batch_generate((s for s in ("one", "two")), output, prefix)
    assert paths == [
        str(output / (prefix + "_1.png")),
        str(output / (prefix + "_2.png")),
    ]
    for path in paths:
        with Image.open(path) as image:
            assert image.format == "PNG"
            image.verify()


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "dangling"])
def test_later_batch_conflict_preflight_writes_nothing(tmp_path, kind):
    path = tmp_path / "qr_2.png"
    target = make_existing(path, kind)
    with pytest.raises(FileExistsError):
        batch_generate(["first", "second"], tmp_path)
    assert not (tmp_path / "qr_1.png").exists()
    assert_existing(path, target, kind)


def test_empty_batch_preserves_existing_return_contract(tmp_path):
    output = tmp_path / "empty"
    assert batch_generate(iter(()), output) == []
    assert output.is_dir()


def test_selected_directory_symlink_is_supported(tmp_path):
    directory = tmp_path / "directory"
    directory.mkdir()
    selected = tmp_path / "selected"
    selected.symlink_to(directory, target_is_directory=True)
    assert batch_generate(["data"], selected) == [str(selected / "qr_1.png")]
    assert (directory / "qr_1.png").is_file()


@pytest.mark.parametrize("kind", ["file", "symlink", "dangling"])
def test_creation_race_cannot_replace_entry(tmp_path, monkeypatch, kind):
    import qrcode_generator.generator as generator

    output = tmp_path / "raced.png"
    link = os.link
    targets = []

    def race(staged, destination):
        targets.append(make_existing(destination, kind))
        link(staged, destination)

    monkeypatch.setattr(generator.os, "link", race)
    with pytest.raises(FileExistsError):
        generate_qr("data", output)
    assert_existing(output, targets[0], kind)
    assert not list(tmp_path.glob(".qrgen-*"))


def test_hardlink_failure_has_no_unsafe_fallback(tmp_path, monkeypatch):
    import qrcode_generator.generator as generator

    def unsupported(*args):
        raise OSError(errno.EOPNOTSUPP, "synthetic unsupported hard link")

    monkeypatch.setattr(generator.os, "link", unsupported)
    with pytest.raises(OSError, match="unsupported"):
        generate_qr("data", tmp_path / "output.png")
    assert not list(tmp_path.iterdir())


def test_concurrent_writers_publish_exactly_one_image(tmp_path):
    output = tmp_path / "shared.png"

    def attempt(index):
        try:
            generate_qr("synthetic-" + str(index), output)
            return "created"
        except FileExistsError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(attempt, range(24)))
    assert results.count("created") == 1
    assert results.count("conflict") == 23
    assert sorted(p.name for p in tmp_path.iterdir()) == ["shared.png"]
    with Image.open(output) as image:
        image.verify()


def test_serialization_failure_cleans_staging(tmp_path, monkeypatch):
    import qrcode.image.pil

    def fail(self, path, **kwargs):
        Path(path).write_bytes(b"partial-image")
        raise OSError("synthetic save failure")

    monkeypatch.setattr(qrcode.image.pil.PilImage, "save", fail)
    with pytest.raises(OSError, match="save failure"):
        generate_qr("data", tmp_path / "output.png")
    assert not list(tmp_path.iterdir())


def test_late_batch_failure_keeps_only_completed_files(tmp_path, monkeypatch):
    import qrcode_generator.generator as generator

    original = generator.generate_qr

    def fail_second(data, output):
        if data == "second":
            raise OSError("synthetic second failure")
        return original(data, output)

    monkeypatch.setattr(generator, "generate_qr", fail_second)
    with pytest.raises(OSError, match="second failure"):
        batch_generate(["first", "second"], tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["qr_1.png"]


@pytest.mark.parametrize("command", ["generate", "wifi", "batch"])
def test_cli_repeated_output_reports_error(tmp_path, command):
    runner = CliRunner()
    if command == "generate":
        args = ["generate", "-d", "data", "-o", str(tmp_path / "out.png")]
    elif command == "wifi":
        args = [
            "wifi",
            "--ssid",
            "Cafe;Guest",
            "--password",
            "synthetic",
            "-o",
            str(tmp_path / "out.png"),
        ]
    else:
        input_file = tmp_path / "input.txt"
        input_file.write_text("one\ntwo\n", encoding="utf-8")
        args = ["batch", "-f", str(input_file), "-o", str(tmp_path / "batch")]
    assert runner.invoke(main, args).exit_code == 0
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.png")}
    result = runner.invoke(main, args)
    assert result.exit_code != 0
    assert "Error:" in result.output
    assert "saved" not in result.output and "Generated" not in result.output
    assert all(path.read_bytes() == data for path, data in before.items())


def test_cli_missing_input_is_readable_error(tmp_path):
    result = CliRunner().invoke(main, ["batch", "-f", str(tmp_path / "missing")])
    assert result.exit_code != 0
    assert "Error:" in result.output


@pytest.mark.parametrize("kind", ["file", "symlink-file", "dangling"])
def test_output_directory_entry_is_not_replaced(tmp_path, kind):
    if kind == "file":
        directory = tmp_path / "output"
        directory.write_bytes(b"keep")
    elif kind == "symlink-file":
        target = tmp_path / "target.txt"
        target.write_bytes(b"keep")
        directory = tmp_path / "output"
        directory.symlink_to(target)
    else:
        directory = tmp_path / "output"
        directory.symlink_to(tmp_path / "missing")
    with pytest.raises(NotADirectoryError, match="not a directory") as excinfo:
        batch_generate(["new"], directory)
    assert str(directory) in str(excinfo.value)
    assert f"{directory}{os.sep}qr_1.png" not in str(excinfo.value)
    if kind == "dangling":
        assert directory.is_symlink()
        assert not directory.exists()
    elif kind == "file":
        assert directory.read_bytes() == b"keep"
    else:
        assert directory.is_symlink()
        assert (tmp_path / "target.txt").read_bytes() == b"keep"
    assert list(tmp_path.glob("*.png")) == []
    assert not list(tmp_path.glob(".qrgen-*"))


@pytest.mark.parametrize("kind", ["file", "dangling"])
def test_generate_parent_entry_is_not_replaced(tmp_path, kind):
    parent = tmp_path / "parent"
    if kind == "file":
        parent.write_bytes(b"keep")
    else:
        parent.symlink_to(tmp_path / "missing")
    with pytest.raises(NotADirectoryError, match="not a directory") as excinfo:
        generate_qr("data", parent / "out.png")
    assert str(parent) in str(excinfo.value)
    assert "out.png" not in str(excinfo.value)
    if kind == "file":
        assert parent.read_bytes() == b"keep"
    else:
        assert parent.is_symlink()
        assert not parent.exists()
    assert not list(tmp_path.glob(".qrgen-*"))


def test_bad_batch_directory_does_not_consume_input(tmp_path):
    seen = []

    def source():
        seen.append("pulled")
        yield "data"

    target = tmp_path / "file"
    target.write_bytes(b"keep")
    with pytest.raises(NotADirectoryError):
        batch_generate(source(), target)
    assert seen == []
    assert target.read_bytes() == b"keep"


def test_customization_and_path_return_unchanged(tmp_path):
    path = tmp_path / "sub" / "image.png"
    result = generate_qr(
        "data", path, box_size=4, border=2, fill_color="navy", back_color="white"
    )
    assert result == path
    assert isinstance(result, Path)
    with Image.open(result) as image:
        assert image.format == "PNG"
        assert image.width == 100
