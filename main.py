import os
import subprocess
import sys
import io
import shutil
from pathlib import Path

def setup_utf8_encoding():
    """Configura o encoding para UTF-8 no terminal"""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def limpar_pasta_done():
    """Limpa apenas a pasta done antes de iniciar o processamento"""
    try:
        base_dir = Path(__file__).resolve().parent
        done_path = base_dir / "src" / "output" / "gerador" / "done"
        
        if done_path.exists():
            shutil.rmtree(done_path)
            print(f"🧹 Pasta 'done' removida: {done_path}")
        
        done_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Pasta 'done' criada: {done_path}")
    except Exception as e:
        print(f"⚠️  Erro ao limpar/criar pasta done: {e}")

def load_env_file(env_path='.env'):
    """Carrega .env usando o utilitário `src.settings.env_loader` e retorna o dicionário de variáveis de ambiente."""
    try:
        try:
            from src.settings.env_loader import load_env
        except Exception:
            from settings.env_loader import load_env
        load_env(path=env_path, verbose=False)
    except Exception as e:
        print(f"Erro ao carregar .env: {e}")
        sys.exit(1)

    # retorna o snapshot atual do ambiente (apenas para compatibilidade)
    return dict(os.environ)

def run_script(script_path, script_name):
    """
    Executa um script Python com encoding UTF-8
    """
    if not os.path.exists(script_path):
        print(f"Erro: Arquivo {script_path} não encontrado!")
        return False
    
    print(f"\n{'='*50}")
    print(f"Executando: {script_name}")
    print(f"Caminho: {script_path}")
    print(f"{'='*50}")
    
    try:
        # Configura environment para UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        # Garante que o pacote src seja encontrado
        project_root = str(Path(__file__).resolve().parent)
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')
        
        # Executa o script com encoding UTF-8
        result = subprocess.run(
            [sys.executable, "-X", "utf8", script_path], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            env=env,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"SUCESSO: {script_name} executado com sucesso!")
            if result.stdout:
                print(f"Saída: {result.stdout}")
            return True
        else:
            print(f"ERRO: Erro ao executar {script_name}")
            print(f"Código de saída: {result.returncode}")
            if result.stderr:
                print(f"Erro: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"ERRO: Timeout ao executar {script_name}")
        return False
    except Exception as e:
        print(f"ERRO: Erro inesperado ao executar {script_name}: {e}")
        return False

def main():
    """
    Função principal que carrega o .env e executa os scripts na sequência
    """
    # Configura encoding UTF-8
    setup_utf8_encoding()
    
    print("🚀 Iniciando execução dos scripts...")
    
    # Limpar apenas a pasta done
    print("\n🧹 Limpando pasta done...")
    limpar_pasta_done()
    
    # Carrega as configurações do .env
    config = load_env_file()

    # Define caminhos padrão relativos ao projeto, permitindo override pelo .env
    base_dir = Path(__file__).resolve().parent
    defaults = {
        'bo': base_dir / 'src' / 'main' / 'geracao' / 'coletas' / 'bo_download.py',
        'cnh': base_dir / 'src' / 'main' / 'geracao' / 'coletas' / 'driverLicense.py',
        'contrato': base_dir / 'src' / 'main' / 'geracao' / 'coletas' / 'rentalDocument.py',
        'docVeiculo': base_dir / 'src' / 'main' / 'geracao' / 'coletas' / 'vehicleDocument.py',
        'generatePDF': base_dir / 'src' / 'main' / 'geracao' / 'gerador' / 'generatePDF.py',
        'mergePDF': base_dir / 'src' / 'main' / 'geracao' / 'gerador' / 'mergePDF.py',
    }

    # Preenche config com defaults quando faltarem
    for key, path in defaults.items():
        if not config.get(key):
            config[key] = str(path)
    
    # Define a sequência de execução na ordem correta
    execution_sequence = [
        ('bo', 'Download do BO'),
        ('cnh', 'Coleta de CNH'),
        ('contrato', 'Coleta de Contrato'),
        ('docVeiculo', 'Coleta de Documento do Veículo'),
        ('generatePDF', 'Geração de PDF Final'),
        ('mergePDF', 'Merge de PDFs')
    ]
    
    # Verifica se todos os scripts existem antes de executar
    missing_scripts = []
    for script_key, script_name in execution_sequence:
        script_path = config.get(script_key)
        if not script_path or not os.path.exists(script_path):
            missing_scripts.append((script_key, script_path))
    
    if missing_scripts:
        print("Erro: Os seguintes scripts não foram encontrados:")
        for key, path in missing_scripts:
            print(f"  {key}: {path}")
        sys.exit(1)
    
    # Executa os scripts na sequência
    successful_scripts = []
    failed_scripts = []
    
    for script_key, script_name in execution_sequence:
        script_path = config[script_key]
        
        if run_script(script_path, script_name):
            successful_scripts.append(script_name)
        else:
            failed_scripts.append(script_name)
            # Pergunta se deve continuar apesar do erro
            continuar = input(f"\nErro ao executar {script_name}. Deseja continuar? (s/N): ")
            if continuar.lower() != 's':
                print("Execução interrompida pelo usuário.")
                break
    
    # Relatório final
    print(f"\n{'='*50}")
    print("RELATÓRIO DE EXECUÇÃO")
    print(f"{'='*50}")
    print(f"Scripts executados com sucesso: {len(successful_scripts)}")
    for script in successful_scripts:
        print(f"  SUCESSO: {script}")
    
    if failed_scripts:
        print(f"Scripts com erro: {len(failed_scripts)}")
        for script in failed_scripts:
            print(f"  ERRO: {script}")
    else:
        print("Todos os scripts foram executados com sucesso!")
    
    print(f"{'='*50}")

if __name__ == "__main__":
    main()