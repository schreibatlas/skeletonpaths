from pathlib import Path

import skeletonpaths


def test_package_does_not_import_inkgrammar():
    root = Path(skeletonpaths.__file__).resolve().parent
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import inkgrammar" not in text
        assert "from inkgrammar" not in text


def test_source_checkout_has_version_string():
    assert isinstance(skeletonpaths.__version__, str)
    assert skeletonpaths.__version__
