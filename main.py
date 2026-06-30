import os
import mimetypes
from pathlib import Path
import chardet
from datetime import datetime
import pathspec
import argparse

LOCK_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'uv.lock', 'poetry.lock', 'Pipfile.lock',
    'Gemfile.lock', 'composer.lock', 'Cargo.lock',
}

class FileConsolidator:
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
            self._extra_spec = pathspec.PathSpec.from_lines('gitignore', self.extra_ignore)
        else:
            self._extra_spec = None


    def _load_gitignore_spec(self):
        patterns = []
        for gitignore_path in self.input_directory.rglob('.gitignore'):
            try:
                patterns.extend(gitignore_path.read_text(encoding='utf-8', errors='ignore').splitlines())
            except Exception:
                pass
        if not patterns:
            return None
        return pathspec.PathSpec.from_lines('gitignore', patterns)

    def detect_encoding(self, file_path):
        """Detecta a codificação do arquivo"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Lê apenas os primeiros 10KB
                result = chardet.detect(raw_data)
                return result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
        except:
            return 'utf-8'

    def is_text_file(self, file_path):
        """Verifica se o arquivo é de texto/código"""
        file_path = Path(file_path)
        
        # Verifica extensão
        if file_path.suffix.lower() in self.text_extensions:
            return True
            
        # Verifica MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('text/'):
            return True
            
        # Para arquivos sem extensão, tenta detectar se é texto
        if not file_path.suffix:
            try:
                encoding = self.detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    sample = f.read(512)
                    # Se conseguir ler e tiver caracteres imprimíveis, considera texto
                    return len(sample.strip()) > 0 and sample.isprintable()
            except:
                return False
                
        return False

    def should_ignore(self, path):
        """Verifica se o arquivo/diretório deve ser ignorado"""
        path = Path(path)

        if path.name in LOCK_FILES:
            return True

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

    def read_file_content(self, file_path):
        """Lê o conteúdo do arquivo com tratamento de encoding"""
        try:
            encoding = self.detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                return f.read()
        except Exception as e:
            return f"[ERRO AO LER ARQUIVO: {str(e)}]"

    def get_file_info(self, file_path):
        """Obtém informações básicas do arquivo"""
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
        except:
            return {'size': 0, 'modified': 'Desconhecido'}

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

    def _print_summary(self, processed, skipped_count, total_chars):
        print(f"\n✅ Consolidação concluída!")
        print(f"📁 Arquivos processados: {processed}")
        print(f"⏭️  Arquivos pulados: {skipped_count}")
        print(f"📄 Arquivo de saída: {self.output_file}")
        print(f"💾 Tamanho final: {os.path.getsize(self.output_file):,} bytes")
        print(f"🔢 Estimativa de tokens: ~{total_chars // 4:,}")

    def _write_txt(self, included, skipped):
        lines = []
        lines.append(f"# CONSOLIDAÇÃO DE ARQUIVOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"# Diretório base: {self.input_directory.absolute()}\n")
        lines.append('=' * 80 + '\n\n')

        for file_path, file_info in included:
            relative = file_path.relative_to(self.input_directory)
            content = self.read_file_content(file_path)
            print(f"  Processando: {relative}")
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

    def _write_xml(self, included):
        lines = ['<documents>\n']

        for i, (file_path, file_info) in enumerate(included, 1):
            relative = file_path.relative_to(self.input_directory)
            content = self.read_file_content(file_path)
            print(f"  Processando: {relative}")
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

    def dry_run(self, max_file_size_mb=10):
        """Mostra arquivos que seriam incluídos sem gerar saída."""
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

    def consolidate_files(self, max_file_size_mb=10):
        included, skipped = self._collect_files(max_file_size_mb)

        if self.output_format == 'xml':
            self._write_xml(included)
        else:
            self._write_txt(included, skipped)

def main():
    parser = argparse.ArgumentParser(
        description='Consolida arquivos de código em um único arquivo para uso com LLMs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py ./meu-projeto
  python main.py ./meu-projeto --dry-run
  python main.py ./meu-projeto --ignore "*.test.js" --ignore "coverage/"
  python main.py ./meu-projeto --no-gitignore --max-size 5
  python main.py ./meu-projeto --format xml -o para-claude.txt
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
        help='Formato de saída: txt (padrão) ou xml (recomendado para Claude)'
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
        extra_ignore=[p for p in args.ignore if p.strip()],
        use_gitignore=not args.no_gitignore,
        output_format=args.format,
    )

    if args.dry_run:
        consolidator.dry_run(args.max_size)
    else:
        consolidator.consolidate_files(args.max_size)

if __name__ == "__main__":
    main()