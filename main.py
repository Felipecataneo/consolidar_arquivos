import os
import mimetypes
from pathlib import Path
import chardet
from datetime import datetime

class FileConsolidator:
    def __init__(self, input_directory=".", output_file="consolidated_files.txt"):
        self.input_directory = Path(input_directory)
        self.output_file = output_file
        
        # Extensões de arquivo que geralmente contêm código/texto
        self.text_extensions = {
            '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.hpp',
            '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx', '.tsx',
            '.vue', '.svelte', '.sql', '.sh', '.bat', '.ps1', '.yaml', '.yml',
            '.json', '.xml', '.md', '.txt', '.csv', '.ini', '.cfg', '.conf',
            '.env', '.gitignore', '.dockerfile', '.makefile', '.cmake',
            '.r', '.scala', '.clj', '.ex', '.exs', '.dart', '.lua', '.pl',
            '.asm', '.s', '.vb', '.cs', '.fs', '.ml', '.hs', '.elm'
        }
        
        # Arquivos que devem ser ignorados
        self.ignore_patterns = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules', 
            '.DS_Store', 'Thumbs.db', '.vscode', '.idea',
            '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe',
            '*.class', '*.jar', '*.war', '*.ear'
        }

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
        
        # Ignora arquivos/pastas ocultos (começam com .)
        if path.name.startswith('.') and path.name not in {'.env', '.gitignore'}:
            return True
            
        # Verifica padrões de ignore
        for pattern in self.ignore_patterns:
            if pattern in str(path).lower():
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

    def consolidate_files(self, max_file_size_mb=10):
        """Consolida todos os arquivos em um único arquivo"""
        max_size_bytes = max_file_size_mb * 1024 * 1024
        consolidated_content = []
        processed_files = 0
        skipped_files = 0
        
        # Header do arquivo consolidado
        header = f"""# CONSOLIDAÇÃO DE ARQUIVOS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Diretório base: {self.input_directory.absolute()}
# Gerado automaticamente para análise por LLM
{'='*80}

"""
        consolidated_content.append(header)
        
        # Percorre todos os arquivos recursivamente
        for file_path in self.input_directory.rglob('*'):
            if file_path.is_file() and not self.should_ignore(file_path):
                
                # Verifica se é arquivo de texto
                if not self.is_text_file(file_path):
                    skipped_files += 1
                    continue
                
                # Verifica tamanho do arquivo
                file_info = self.get_file_info(file_path)
                if file_info['size'] > max_size_bytes:
                    consolidated_content.append(f"\n[ARQUIVO MUITO GRANDE - PULADO]: {file_path.relative_to(self.input_directory)}\n")
                    skipped_files += 1
                    continue
                
                # Lê o conteúdo do arquivo
                content = self.read_file_content(file_path)
                
                # Adiciona separador e informações do arquivo
                relative_path = file_path.relative_to(self.input_directory)
                file_section = f"""
{'='*80}
ARQUIVO: {relative_path}
TAMANHO: {file_info['size']} bytes
MODIFICADO: {file_info['modified']}
{'='*80}

{content}

"""
                consolidated_content.append(file_section)
                processed_files += 1
                
                print(f"Processado: {relative_path}")
        
        # Escreve arquivo consolidado
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.writelines(consolidated_content)
                
            # Footer com estatísticas
            footer = f"""
{'='*80}
RESUMO DA CONSOLIDAÇÃO
{'='*80}
Total de arquivos processados: {processed_files}
Total de arquivos pulados: {skipped_files}
Arquivo de saída: {self.output_file}
Tamanho final: {os.path.getsize(self.output_file)} bytes
{'='*80}
"""
            
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(footer)
                
            print(f"\n✅ Consolidação concluída!")
            print(f"📁 Arquivos processados: {processed_files}")
            print(f"⏭️  Arquivos pulados: {skipped_files}")
            print(f"📄 Arquivo de saída: {self.output_file}")
            print(f"💾 Tamanho final: {os.path.getsize(self.output_file)} bytes")
            
        except Exception as e:
            print(f"❌ Erro ao escrever arquivo consolidado: {e}")

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