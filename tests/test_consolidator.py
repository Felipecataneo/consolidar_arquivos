import pytest
import tempfile
from pathlib import Path
from main import FileConsolidator, LOCK_FILES


@pytest.fixture
def tmp_project(tmp_path):
    """Cria um projeto temporário para testes."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
    (tmp_path / "README.md").write_text("# Projeto")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lodash.js").write_text("// lib")
    (tmp_path / "package-lock.json").write_text("{}")
    (tmp_path / ".gitignore").write_text("dist/\n*.log\n")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "bundle.js").write_text("// built")
    (tmp_path / "app.log").write_text("log entry")
    return tmp_path
