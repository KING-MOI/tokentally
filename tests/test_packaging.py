import tomllib
from pathlib import Path

import tokentally


def test_package_version_matches_pyproject() -> None:
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    meta = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert meta["project"]["version"] == tokentally.__version__
