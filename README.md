# File Consolidator for LLMs

Este projeto é um consolidador de arquivos de texto e código, ideal para preparar diretórios inteiros para análise por modelos de linguagem (LLMs), como GPT.

## 🧩 O que ele faz?
- Lê recursivamente todos os arquivos em um diretório.
- Detecta codificação automaticamente.
- Ignora arquivos binários, ocultos ou muito grandes.
- Consolida arquivos de texto e código em um único arquivo `.txt`.
- Inclui informações como caminho relativo, tamanho e data de modificação.

## 📂 Exemplos de arquivos aceitos
Arquivos com extensões como `.py`, `.js`, `.html`, `.css`, `.json`, `.md`, `.sh`, entre muitos outros.

## 🚫 Arquivos ignorados
- Binários: `.exe`, `.dll`, `.class`, etc.
- Diretórios comuns como `__pycache__`, `.git`, `node_modules`.
- Arquivos ocultos (exceto `.env` e `.gitignore`).
- Arquivos maiores que o limite definido (padrão: 10 MB).

## 🚀 Como usar

### Requisitos
- Python 3.7+
- Biblioteca `chardet` (instale com `pip install chardet`)

### Execução
```bash
python file_consolidator.py
```

### Parâmetros interativos
Durante a execução, o script pedirá:
- Diretório de entrada (padrão: diretório atual)
- Nome do arquivo de saída (padrão: `consolidated_files.txt`)
- Tamanho máximo dos arquivos em MB (padrão: 10 MB)

## 📁 Estrutura do arquivo de saída

Cada arquivo consolidado é precedido por um cabeçalho com:
- Caminho relativo
- Tamanho
- Data de modificação

Ao final, é exibido um resumo com estatísticas.

## 📜 Exemplo de saída

```
================================================================================
ARQUIVO: src/main.py
TAMANHO: 2048 bytes
MODIFICADO: 2025-06-01 14:22:03
================================================================================

def main():
    print("Olá mundo")
```

## 🛠️ Customização
Você pode modificar:
- Extensões de arquivos permitidas (`self.text_extensions`)
- Padrões ignorados (`self.ignore_patterns`)
- Tamanho máximo permitido

## 📄 Licença
MIT License