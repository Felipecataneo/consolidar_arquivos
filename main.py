import os
import mimetypes
from pathlib import Path
import chardet
from datetime import datetime
import pathspec

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

    def consolidate_files(self, max_file_size_mb=10):
        included, skipped = self._collect_files(max_file_size_mb)

        if self.output_format == 'xml':
            self._write_xml(included)
        else:
            self._write_txt(included, skipped)

def main():
    print("🔄 Consolidador de Arquivos para LLM")
    print("-" * 40)
    
    # Configurações
    input_dir = input("📂 Diretório de entrada (. para atual): ").strip() or "."
    output_file = input("📝 Nome do arquivo de saída (consolidated_files.txt): ").strip() or "consolidated_files.txt"
    max_size = input("📏 Tamanho máximo por arquivo em MB (10): ").strip()
    
    try:
        max_size = int(max_size) if max_size else 10
    except ValueError:
        max_size = 10
    
    # Cria o consolidador e executa
    consolidator = FileConsolidator(input_dir, output_file)
    consolidator.consolidate_files(max_size)

if __name__ == "__main__":
    main()