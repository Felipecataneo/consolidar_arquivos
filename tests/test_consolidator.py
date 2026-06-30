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


def test_collect_files_inclui_codigo(tmp_project):
    c = FileConsolidator(str(tmp_project))
    included, skipped = c._collect_files()
    paths = [str(f.relative_to(tmp_project)) for f, _ in included]
    assert "src/main.py" in paths
    assert "src/utils.py" in paths
    assert "README.md" in paths


def test_collect_files_exclui_node_modules(tmp_project):
    c = FileConsolidator(str(tmp_project))
    included, _ = c._collect_files()
    paths = [str(f.relative_to(tmp_project)) for f, _ in included]
    assert not any("node_modules" in p for p in paths)


def test_collect_files_exclui_lock(tmp_project):
    c = FileConsolidator(str(tmp_project))
    included, _ = c._collect_files()
    names = [f.name for f, _ in included]
    assert "package-lock.json" not in names


def test_collect_files_exclui_gitignored(tmp_project):
    c = FileConsolidator(str(tmp_project), use_gitignore=True)
    included, _ = c._collect_files()
    paths = [str(f.relative_to(tmp_project)) for f, _ in included]
    assert not any("dist" in p for p in paths)
    assert "app.log" not in paths


def test_dry_run_nao_cria_arquivo(tmp_project, capsys):
    output = str(tmp_project / "output.txt")
    c = FileConsolidator(str(tmp_project), output_file=output)
    c.dry_run()
    assert not Path(output).exists()


def test_dry_run_imprime_arquivos(tmp_project, capsys):
    c = FileConsolidator(str(tmp_project))
    c.dry_run()
    captured = capsys.readouterr()
    assert "src/main.py" in captured.out
    assert "tokens" in captured.out.lower()


def test_formato_xml(tmp_project, tmp_path):
    output = str(tmp_path / "out.xml")
    c = FileConsolidator(str(tmp_project), output_file=output, output_format="xml")
    c.consolidate_files()
    content = Path(output).read_text()
    assert "<documents>" in content
    assert "<document index=" in content
    assert "<source>" in content
    assert "<document_content>" in content
    assert "</documents>" in content
