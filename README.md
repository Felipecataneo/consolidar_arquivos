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
