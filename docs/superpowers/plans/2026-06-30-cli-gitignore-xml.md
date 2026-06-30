# CLI + gitignore + XML Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade o consolidador com suporte a .gitignore, exclusão automática de lock files, CLI com argparse, dry-run com estimativa de tokens, e formato de saída XML.

**Architecture:** Todo o código fica em `main.py`. A classe `FileConsolidator` ganha novos parâmetros e métodos; a função `main()` é substituída por argparse. A lógica de coleta de arquivos é extraída para `_collect_files()`, desacoplando-a da escrita.

**Tech Stack:** Python 3.12+, `chardet` (existente), `pathspec` (novo).

---

## Estrutura de arquivos

- Modify: `main.py` — refatoração completa da classe e do `main()`
- Modify: `requirements.txt` — adicionar `pathspec`
- Modify: `pyproject.toml` — adicionar `pathspec>=0.12` nas dependências
- Create: `tests/test_consolidator.py` — testes unitários
- Modify: `README.md` — atualizar documentação

---

### Task 1: Adicionar pathspec e criar estrutura de testes

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/test_consolidator.py`

- [ ] **Step 1: Adicionar pathspec às dependências**

Em `requirements.txt`, adicionar linha:
```
pathspec
```

Em `pyproject.toml`, alterar `dependencies`:
```toml
dependencies = [
    "chardet>=5.2.0",
    "pathspec>=0.12",
]
```

- [ ] **Step 2: Instalar dependência**

```bash
pip install pathspec
```

Ou se usar uv:
```bash
uv add pathspec
```

- [ ] **Step 3: Criar estrutura de testes**

Criar `tests/__init__.py` vazio.

Criar `tests/test_consolidator.py`:
```python
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
```

- [ ] **Step 4: Verificar que o arquivo de teste pode ser importado**

```bash
cd /home/felipe/Documentos/repositorios/consolidar_arquivos
python -c "import pathspec; print('ok')"
```

Esperado: `ok`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pyproject.toml tests/
git commit -m "chore: add pathspec dependency and test scaffold"
```

---

### Task 2: Refatorar lógica de ignore com gitignore e lock files

**Files:**
- Modify: `main.py` — `__init__`, `_load_gitignore_spec`, `should_ignore`
- Modify: `tests/test_consolidator.py`

- [ ] **Step 1: Escrever testes que falham**

Adicionar ao `tests/test_consolidator.py`:
```python
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
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
pytest tests/test_consolidator.py -v
```

Esperado: vários FAILED (LOCK_FILES não existe, use_gitignore não é parâmetro, etc.)

- [ ] **Step 3: Implementar LOCK_FILES e refatorar __init__ e should_ignore**

No topo de `main.py`, após os imports, adicionar:
```python
import pathspec

LOCK_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'uv.lock', 'poetry.lock', 'Pipfile.lock',
    'Gemfile.lock', 'composer.lock', 'Cargo.lock',
}
```

Substituir `__init__` por:
```python
def __init__(self, input_directory=".", output_file="consolidated_files.txt",
             extra_ignore=None, use_gitignore=True, output_format="txt"):
    self.input_directory = Path(input_directory)
    self.output_file = output_file
    self.output_format = output_format
    self.extra_ignore = extra_ignore or []

    self.text_extensions = {
        '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.hpp',
        '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx', '.tsx',
        '.vue', '.svelte', '.sql', '.sh', '.bat', '.ps1', '.yaml', '.yml',
        '.json', '.xml', '.md', '.txt', '.csv', '.ini', '.cfg', '.conf',
        '.env', '.gitignore', '.dockerfile', '.makefile', '.cmake',
        '.r', '.scala', '.clj', '.ex', '.exs', '.dart', '.lua', '.pl',
        '.asm', '.s', '.vb', '.cs', '.fs', '.ml', '.hs', '.elm'
    }

    self._ignore_dirs = {
        '__pycache__', '.git', '.svn', '.hg', 'node_modules',
        '.venv', 'venv', 'env', '.vscode', '.idea',
    }

    self._gitignore_spec = self._load_gitignore_spec() if use_gitignore else None

    if self.extra_ignore:
        self._extra_spec = pathspec.PathSpec.from_lines('gitwildmatch', self.extra_ignore)
    else:
        self._extra_spec = None
```

Adicionar método `_load_gitignore_spec`:
```python
def _load_gitignore_spec(self):
    patterns = []
    for gitignore_path in self.input_directory.rglob('.gitignore'):
        try:
            patterns.extend(gitignore_path.read_text(encoding='utf-8', errors='ignore').splitlines())
        except Exception:
            pass
    if not patterns:
        return None
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)
```

Substituir método `should_ignore`:
```python
def should_ignore(self, path):
    path = Path(path)

    if path.name in LOCK_FILES:
        return True

    # Verifica segmentos do caminho (node_modules, .venv, etc.)
    for part in path.parts:
        if part in self._ignore_dirs:
            return True
        if part.startswith('.') and part not in {'.env', '.gitignore'}:
            return True

    try:
        relative = str(path.relative_to(self.input_directory))
    except ValueError:
        return False

    if self._gitignore_spec and self._gitignore_spec.match_file(relative):
        return True

    if self._extra_spec and self._extra_spec.match_file(relative):
        return True

    return False
```

Remover o atributo `self.ignore_patterns` do `__init__` original (não é mais usado).

- [ ] **Step 4: Rodar testes**

```bash
pytest tests/test_consolidator.py -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_consolidator.py
git commit -m "feat: gitignore support, lock file exclusion, precise dir matching"
```

---

### Task 3: Extrair _collect_files() e refatorar consolidate_files

**Files:**
- Modify: `main.py` — novos métodos `_collect_files`, `_write_txt`, `_print_summary`; refatorar `consolidate_files`
- Modify: `tests/test_consolidator.py`

- [ ] **Step 1: Escrever testes para _collect_files**

Adicionar ao `tests/test_consolidator.py`:
```python
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
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
pytest tests/test_consolidator.py::test_collect_files_inclui_codigo -v
```

Esperado: FAILED (_collect_files não existe)

- [ ] **Step 3: Implementar _collect_files e refatorar consolidate_files**

Adicionar método `_collect_files` na classe:
```python
def _collect_files(self, max_file_size_mb=10):
    max_size_bytes = max_file_size_mb * 1024 * 1024
    included = []
    skipped = []

    for file_path in sorted(self.input_directory.rglob('*')):
        if not file_path.is_file():
            continue
        if self.should_ignore(file_path):
            skipped.append(file_path)
            continue
        if not self.is_text_file(file_path):
            skipped.append(file_path)
            continue
        file_info = self.get_file_info(file_path)
        if file_info['size'] > max_size_bytes:
            skipped.append(file_path)
            continue
        included.append((file_path, file_info))

    return included, skipped
```

Adicionar método `_print_summary`:
```python
def _print_summary(self, processed, skipped_count, total_chars):
    print(f"\n✅ Consolidação concluída!")
    print(f"📁 Arquivos processados: {processed}")
    print(f"⏭️  Arquivos pulados: {skipped_count}")
    print(f"📄 Arquivo de saída: {self.output_file}")
    print(f"💾 Tamanho final: {os.path.getsize(self.output_file):,} bytes")
    print(f"🔢 Estimativa de tokens: ~{total_chars // 4:,}")
```

Substituir `consolidate_files` por uma versão que delega para `_collect_files`:
```python
def consolidate_files(self, max_file_size_mb=10):
    included, skipped = self._collect_files(max_file_size_mb)

    if self.output_format == 'xml':
        self._write_xml(included)
    else:
        self._write_txt(included, skipped)
```

Adicionar `_write_txt` (extrai a lógica existente de escrita):
```python
def _write_txt(self, included, skipped):
    lines = []
    lines.append(f"# CONSOLIDAÇÃO DE ARQUIVOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"# Diretório base: {self.input_directory.absolute()}\n")
    lines.append('=' * 80 + '\n\n')

    for file_path, file_info in included:
        relative = file_path.relative_to(self.input_directory)
        content = self.read_file_content(file_path)
        lines.append(f"\n{'=' * 80}\n")
        lines.append(f"ARQUIVO: {relative}\n")
        lines.append(f"TAMANHO: {file_info['size']} bytes\n")
        lines.append(f"MODIFICADO: {file_info['modified']}\n")
        lines.append(f"{'=' * 80}\n\n")
        lines.append(content)
        lines.append('\n\n')

    total_chars = sum(info['size'] for _, info in included)
    lines.append(f"\n{'=' * 80}\n")
    lines.append("RESUMO\n")
    lines.append(f"{'=' * 80}\n")
    lines.append(f"Arquivos processados: {len(included)}\n")
    lines.append(f"Arquivos pulados: {len(skipped)}\n")
    lines.append(f"Estimativa de tokens: ~{total_chars // 4:,}\n")

    try:
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        self._print_summary(len(included), len(skipped), total_chars)
    except Exception as e:
        print(f"❌ Erro ao escrever arquivo consolidado: {e}")
```

- [ ] **Step 4: Rodar todos os testes**

```bash
pytest tests/ -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_consolidator.py
git commit -m "refactor: extract _collect_files and _write_txt for cleaner flow"
```

---

### Task 4: Substituir prompts interativos por CLI com argparse

**Files:**
- Modify: `main.py` — substituir função `main()`

- [ ] **Step 1: Substituir main() pelo CLI argparse**

Substituir a função `main()` inteira por:
```python
def main():
    parser = argparse.ArgumentParser(
        description='Consolida arquivos de código em um único arquivo para uso com LLMs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py ./meu-projeto
  python main.py ./meu-projeto --dry-run
  python main.py ./meu-projeto --format xml -o para-claude.txt
  python main.py ./meu-projeto --ignore "*.test.js" --ignore "coverage/"
  python main.py ./meu-projeto --no-gitignore --max-size 5
        """
    )
    parser.add_argument(
        'directory', nargs='?', default='.',
        help='Diretório de entrada (padrão: diretório atual)'
    )
    parser.add_argument(
        '-o', '--output', default='consolidated_files.txt',
        help='Arquivo de saída (padrão: consolidated_files.txt)'
    )
    parser.add_argument(
        '--max-size', type=float, default=10, metavar='MB',
        help='Tamanho máximo por arquivo em MB (padrão: 10)'
    )
    parser.add_argument(
        '--format', choices=['txt', 'xml'], default='txt',
        help='Formato de saída: txt (padrão) ou xml'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Mostra arquivos que seriam incluídos sem gerar saída'
    )
    parser.add_argument(
        '--ignore', action='append', default=[], metavar='PADRÃO',
        help='Padrão adicional a ignorar (pode repetir)'
    )
    parser.add_argument(
        '--no-gitignore', action='store_true',
        help='Não respeita .gitignore'
    )

    args = parser.parse_args()

    consolidator = FileConsolidator(
        input_directory=args.directory,
        output_file=args.output,
        extra_ignore=args.ignore,
        use_gitignore=not args.no_gitignore,
        output_format=args.format,
    )

    if args.dry_run:
        consolidator.dry_run(args.max_size)
    else:
        consolidator.consolidate_files(args.max_size)
```

Adicionar `import argparse` no topo de `main.py`.

- [ ] **Step 2: Testar o CLI manualmente**

```bash
python main.py --help
```

Esperado: help text com todos os argumentos listados.

```bash
python main.py . --dry-run
```

Esperado: lista de arquivos que seriam incluídos (sem gerar arquivo).

- [ ] **Step 3: Rodar testes para garantir que nada quebrou**

```bash
pytest tests/ -v
```

Esperado: todos PASSED.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: replace interactive prompts with argparse CLI"
```

---

### Task 5: Adicionar dry-run com estimativa de tokens

**Files:**
- Modify: `main.py` — adicionar método `dry_run`
- Modify: `tests/test_consolidator.py`

- [ ] **Step 1: Escrever teste para dry_run**

Adicionar ao `tests/test_consolidator.py`:
```python
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
```

- [ ] **Step 2: Rodar para confirmar que falham**

```bash
pytest tests/test_consolidator.py::test_dry_run_nao_cria_arquivo tests/test_consolidator.py::test_dry_run_imprime_arquivos -v
```

Esperado: FAILED (dry_run não existe)

- [ ] **Step 3: Implementar dry_run**

Adicionar método `dry_run` na classe `FileConsolidator`:
```python
def dry_run(self, max_file_size_mb=10):
    included, skipped = self._collect_files(max_file_size_mb)

    print(f"Arquivos que seriam incluídos ({len(included)}):")
    total_chars = 0
    for file_path, file_info in included:
        relative = file_path.relative_to(self.input_directory)
        size_kb = file_info['size'] / 1024
        print(f"  {str(relative):<60} ({size_kb:.1f} KB)")
        total_chars += file_info['size']

    print(f"\nIgnorados: {len(skipped)} arquivos")

    estimated_tokens = total_chars // 4
    print(f"\nEstimativa de tokens: ~{estimated_tokens:,}")

    if estimated_tokens > 100_000:
        print("⚠️  Contexto muito grande. Considere usar --ignore ou --max-size.")
    elif estimated_tokens > 50_000:
        print("⚠️  Contexto grande. Verifique se todos os arquivos são necessários.")
```

- [ ] **Step 4: Rodar todos os testes**

```bash
pytest tests/ -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_consolidator.py
git commit -m "feat: add --dry-run mode with token estimate"
```

---

### Task 6: Adicionar formato XML

**Files:**
- Modify: `main.py` — adicionar método `_write_xml`
- Modify: `tests/test_consolidator.py`

- [ ] **Step 1: Escrever teste para formato XML**

Adicionar ao `tests/test_consolidator.py`:
```python
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
```

- [ ] **Step 2: Rodar para confirmar que falha**

```bash
pytest tests/test_consolidator.py::test_formato_xml -v
```

Esperado: FAILED (_write_xml não existe)

- [ ] **Step 3: Implementar _write_xml**

Adicionar método `_write_xml` na classe:
```python
def _write_xml(self, included):
    lines = ['<documents>\n']

    for i, (file_path, file_info) in enumerate(included, 1):
        relative = file_path.relative_to(self.input_directory)
        content = self.read_file_content(file_path)
        lines.append(f'<document index="{i}">\n')
        lines.append(f'<source>{relative}</source>\n')
        lines.append('<document_content>\n')
        lines.append(content)
        lines.append('\n</document_content>\n')
        lines.append('</document>\n')

    lines.append('</documents>\n')

    total_chars = sum(info['size'] for _, info in included)
    try:
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        self._print_summary(len(included), 0, total_chars)
    except Exception as e:
        print(f"❌ Erro ao escrever arquivo consolidado: {e}")
```

- [ ] **Step 4: Rodar todos os testes**

```bash
pytest tests/ -v
```

Esperado: todos PASSED.

- [ ] **Step 5: Testar XML manualmente**

```bash
python main.py . --format xml -o saida.xml --dry-run
python main.py . --format xml -o saida.xml
head -20 saida.xml
```

Esperado: estrutura XML com tags corretas.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_consolidator.py
git commit -m "feat: add XML output format for Claude compatibility"
```

---

### Task 7: Atualizar README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Reescrever README com nova documentação**

Substituir o conteúdo de `README.md` por:

````markdown
# File Consolidator for LLMs

Consolida todos os arquivos de código de um diretório em um único arquivo `.txt` ou `.xml`, ideal para inserir projetos inteiros no contexto de um LLM (Claude, GPT, etc.).

## O que ele faz

- Lê recursivamente todos os arquivos de texto/código de um diretório
- Respeita `.gitignore` automaticamente (exclui `node_modules`, `dist`, `build`, etc.)
- Exclui lock files automaticamente (`package-lock.json`, `yarn.lock`, `uv.lock`, etc.)
- Detecta codificação automaticamente
- Ignora arquivos binários, ocultos e muito grandes
- Gera estimativa de tokens para saber se vai caber no contexto
- Suporta formato XML (melhor leitura pelo Claude)

## Instalação

```bash
pip install chardet pathspec
```

Ou com uv:
```bash
uv sync
```

## Uso

```bash
python main.py [diretório] [opções]
```

### Argumentos

| Argumento | Descrição | Padrão |
|-----------|-----------|--------|
| `diretório` | Diretório de entrada | `.` (atual) |
| `-o, --output FILE` | Arquivo de saída | `consolidated_files.txt` |
| `--max-size MB` | Tamanho máximo por arquivo | `10` MB |
| `--format txt\|xml` | Formato de saída | `txt` |
| `--dry-run` | Mostra o que seria incluído sem gerar saída | — |
| `--ignore PADRÃO` | Padrão extra a ignorar (pode repetir) | — |
| `--no-gitignore` | Não respeita `.gitignore` | — |

### Exemplos

```bash
# Consolidar o diretório atual
python main.py .

# Ver o que seria incluído antes de gerar (com estimativa de tokens)
python main.py ./meu-projeto --dry-run

# Gerar formato XML (recomendado para Claude)
python main.py ./meu-projeto --format xml -o para-claude.xml

# Ignorar pastas de testes e coverage
python main.py ./meu-projeto --ignore "tests/" --ignore "coverage/"

# Ignorar arquivos de teste e limitar tamanho
python main.py ./meu-projeto --ignore "*.test.js" --max-size 5

# Não respeitar .gitignore
python main.py ./meu-projeto --no-gitignore
```

## O que é excluído automaticamente

**Diretórios:**
- `node_modules`, `.venv`, `venv`, `env`
- `.git`, `.svn`, `.hg`
- `__pycache__`, `.vscode`, `.idea`
- Qualquer pasta listada no `.gitignore` do projeto

**Lock files:**
- `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- `uv.lock`, `poetry.lock`, `Pipfile.lock`
- `Gemfile.lock`, `composer.lock`, `Cargo.lock`

**Outros:**
- Arquivos binários (`.exe`, `.dll`, `.class`, `.so`, etc.)
- Arquivos ocultos (exceto `.env` e `.gitignore`)
- Arquivos maiores que o limite definido (padrão: 10 MB)

## Formato de saída

### TXT (padrão)
```
================================================================================
ARQUIVO: src/main.py
TAMANHO: 2048 bytes
MODIFICADO: 2025-06-01 14:22:03
================================================================================

def main():
    print("Olá mundo")
```

### XML (--format xml)
```xml
<documents>
<document index="1">
<source>src/main.py</source>
<document_content>
def main():
    print("Olá mundo")
</document_content>
</document>
</documents>
```

## Estimativa de tokens

O `--dry-run` mostra uma estimativa de tokens antes de gerar o arquivo:

```
Arquivos que seriam incluídos (12):
  src/main.py                                                  (1.2 KB)
  src/utils.py                                                 (0.8 KB)
  README.md                                                    (0.5 KB)

Ignorados: 847 arquivos

Estimativa de tokens: ~18.400
```
````

- [ ] **Step 2: Verificar que o README está correto**

```bash
cat README.md
```

- [ ] **Step 3: Commit final**

```bash
git add README.md
git commit -m "docs: update README with new CLI usage and examples"
```
