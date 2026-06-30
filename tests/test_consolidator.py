import pytest
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


def test_ignora_node_modules(tmp_project):
    c = FileConsolidator(str(tmp_project))
    node_mod = tmp_project / "node_modules" / "lodash.js"
    assert c.should_ignore(node_mod) is True


def test_ignora_lock_files(tmp_project):
    c = FileConsolidator(str(tmp_project))
    lock = tmp_project / "package-lock.json"
    assert c.should_ignore(lock) is True


def test_lock_files_set():
    assert "package-lock.json" in LOCK_FILES
    assert "yarn.lock" in LOCK_FILES
    assert "uv.lock" in LOCK_FILES
    assert "poetry.lock" in LOCK_FILES


def test_respeita_gitignore(tmp_project):
    c = FileConsolidator(str(tmp_project), use_gitignore=True)
    dist_file = tmp_project / "dist" / "bundle.js"
    log_file = tmp_project / "app.log"
    assert c.should_ignore(dist_file) is True
    assert c.should_ignore(log_file) is True


def test_nao_ignora_arquivo_normal(tmp_project):
    c = FileConsolidator(str(tmp_project))
    main_py = tmp_project / "src" / "main.py"
    assert c.should_ignore(main_py) is False


def test_ignora_extra_pattern(tmp_project):
    (tmp_project / "src" / "main.test.py").write_text("# test")
    c = FileConsolidator(str(tmp_project), extra_ignore=["*.test.py"])
    test_file = tmp_project / "src" / "main.test.py"
    assert c.should_ignore(test_file) is True


def test_ignora_diretorio_em_qualquer_profundidade(tmp_project):
    nested = tmp_project / "src" / ".git" / "objects" / "file.py"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("# git object")
    c = FileConsolidator(str(tmp_project))
    assert c.should_ignore(nested) is True


def test_ignora_gitignore_quando_desabilitado(tmp_project):
    c = FileConsolidator(str(tmp_project), use_gitignore=False)
    dist_file = tmp_project / "dist" / "bundle.js"
    assert c.should_ignore(dist_file) is False
