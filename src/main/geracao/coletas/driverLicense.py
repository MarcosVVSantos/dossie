import sys
from pathlib import Path

# IMPORTANTE: Configurar sys.path ANTES de qualquer outro import
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os
import requests
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import shutil
import json

# Carrega .env de forma robusta usando src/settings/env_loader.py (com fallback)
try:
    from src.settings.env_loader import load_env
except Exception:
    try:
        from settings.env_loader import load_env
    except Exception:
        # Fallback simples em caso de import falhar (usa dotenv diretamente)
        def load_env(path: str | None = None, required_vars: list | None = None, verbose: bool = False):
            from dotenv import load_dotenv, find_dotenv
            env_path = path or os.environ.get('ENV_PATH') or find_dotenv()
            if env_path:
                load_dotenv(dotenv_path=env_path)
                if verbose:
                    print(f"🔎 Usando .env em: {env_path}")
            else:
                if verbose:
                    print("⚠️ Nenhum arquivo .env encontrado; continuando (variáveis podem estar no ambiente).")
            if required_vars:
                missing = [v for v in required_vars if os.environ.get(v) in (None, '')]
                if missing:
                    raise RuntimeError(f"Faltando variáveis de ambiente: {', '.join(missing)}. Veja .env.example")
            return {v: os.environ.get(v) for v in (required_vars or [])}

# Variáveis obrigatórias para este módulo
required = ['email', 'password', 'backendUrl']
try:
    load_env(required_vars=required, verbose=True)
except Exception as e:
    print(f"✋ Erro ao carregar variáveis de ambiente: {e}")
    raise

# Substitui valores hardcoded por variáveis do .env (com fallback para caminhos relativos ao projeto)
EXCEL_FILE = Path(os.getenv('excel', r"src\utils\Relatório BOs.xlsx")).resolve()
# se a variável 'saida' estiver definida, usa; senão usa pasta output padrão do projeto
OUTPUT_DIR = Path(os.getenv('saida', r"src\output\gerador\cnh")).resolve()

LOGIN_URL = os.getenv('auth_url', 'https://sso.mottu.cloud/realms/Internal/protocol/openid-connect/token')
# Endpoint para buscar CNH — pode compor com backendUrl se preferir
BACKEND_URL = os.getenv('backendUrl', 'https://backend.mottu.cloud/api/v2')
CNH_URL_TEMPLATE = os.getenv('cnh_url_template', BACKEND_URL + '/UsuarioCnh/BuscarUrlCnh/{}?fullUrl=true')

# Credenciais vindas do .env (NÃO deixar segredos hardcoded)
username = os.getenv('email')
password = os.getenv('password')
client_id = os.getenv('client_id', 'mottu-admin')
grant_type = os.getenv('grant_type', 'password')

def limpar_pasta():
    """Limpa a pasta de output antes de executar"""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Pasta {OUTPUT_DIR} limpa e criada")

# Auth handling now centralized in settings.auth
from src.settings.auth import Auth


def obter_token_via_auth() -> str | None:
    auth = Auth()
    token = auth.get_token()
    if not token:
        print("Falha ao obter token via Auth")
    return token

def download_cnh_file(url, local_filename):
    """Faz o download do arquivo da CNH usando URL pré-assinada"""
    try:
        print(f"  📥 Baixando de URL pré-assinada: {url}")
        
        # Para URL pré-assinada, não precisa de token no header
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            
            # Verifica o tipo de conteúdo
            content_type = r.headers.get('content-type', '')
            print(f"  📄 Tipo de conteúdo: {content_type}")
            
            # Determina a extensão do arquivo baseado no content-type
            extension = '.pdf'  # padrão
            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                extension = '.jpg'
            elif 'image/png' in content_type:
                extension = '.png'
            elif 'image/gif' in content_type:
                extension = '.gif'
            elif 'application/pdf' in content_type:
                extension = '.pdf'
            
            # Adiciona a extensão correta ao arquivo
            if not local_filename.endswith(extension):
                local_filename += extension
            
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        print(f"  ✅ Arquivo baixado: {local_filename}")
        return local_filename
    except Exception as e:
        print(f"  ❌ Erro ao baixar arquivo: {e}")
        return None

def get_driver_license_url(userId, token):
    """Obtém a URL da CNH do usuário"""
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        url = CNH_URL_TEMPLATE.format(userId)
        print(f"  🔍 Buscando URL da CNH: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Parse a resposta JSON
            response_data = response.json()
            
            # Verifica se há dataResult na resposta
            if response_data.get('dataResult'):
                cnh_url = response_data['dataResult']
                print(f"  ✅ URL da CNH encontrada: {cnh_url}")
                return cnh_url
            else:
                print(f"  ⚠️ Nenhuma CNH encontrada para o usuário {userId}")
                return None
        elif response.status_code == 401:
            print("  🔐 Token expirado")
            return "TOKEN_EXPIRED"
        else:
            print(f"  ❌ Erro ao buscar URL da CNH: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Erro na requisição da URL da CNH: {e}")
        return None

def converter_imagem_para_pdf(arquivo_imagem, placa, user_id, output_pdf):
    """Converte arquivo de imagem (JPG, PNG) para PDF"""
    try:
        # Cria o PDF
        c = canvas.Canvas(output_pdf, pagesize=letter)
        
        # Adiciona informações no PDF
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "DOCUMENTO DE HABILITAÇÃO - CNH")
        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Placa do Veículo: {placa}")
        c.drawString(100, 710, f"ID do Usuário: {user_id}")
        
        # Adiciona a imagem ao PDF
        try:
            # Lê a imagem
            img = ImageReader(arquivo_imagem)
            img_width, img_height = img.getSize()
            
            # Calcula o tamanho para caber na página mantendo a proporção
            page_width = 500
            page_height = 600
            x_position = 50
            y_position = 100
            
            # Ajusta o tamanho mantendo a proporção
            ratio = min(page_width / img_width, page_height / img_height)
            new_width = img_width * ratio
            new_height = img_height * ratio
            
            # Desenha a imagem no PDF
            c.drawImage(arquivo_imagem, x_position, y_position, 
                       width=new_width, height=new_height,
                       preserveAspectRatio=True)
            
            print(f"  ✅ Imagem convertida para PDF: {output_pdf}")
            
        except Exception as img_error:
            print(f"  ⚠️ Erro ao adicionar imagem ao PDF: {img_error}")
            c.drawString(100, 650, "Erro ao processar a imagem da CNH")
            c.drawString(100, 630, "Arquivo de imagem disponível na pasta")
        
        c.save()
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao converter imagem para PDF: {e}")
        return False

def process_driver_license(userId, plate, token):
    """Processa a CNH do usuário: busca URL, baixa e converte para PDF se necessário"""
    try:
        userId = int(userId)
        plate = str(plate).strip().upper()
        
        print(f"  🔍 Buscando CNH para User: {userId}, Placa: {plate}")
        
        # Buscar URL da CNH
        cnh_url = get_driver_license_url(userId, token)
        
        if cnh_url == "TOKEN_EXPIRED":
            return "TOKEN_EXPIRED"
        
        if not cnh_url:
            print(f"  ⚠️ Nenhuma CNH encontrada para o usuário {userId}")
            return True
        
        # Nome do arquivo temporário
        temp_filename = os.path.join(OUTPUT_DIR, f"temp_cnh_{userId}")
        
        # Fazer download do arquivo usando URL pré-assinada
        print(f"  📥 Baixando CNH de URL pré-assinada")
        downloaded_file = download_cnh_file(cnh_url, temp_filename)
        
        if not downloaded_file:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            return False
        
        # Verifica o tipo de arquivo baixado
        file_extension = os.path.splitext(downloaded_file)[1].lower()
        
        # Caminho final do arquivo
        final_filename = os.path.join(OUTPUT_DIR, f"{plate}_{userId}.pdf")
        
        if file_extension == '.pdf':
            # Se já é PDF, apenas move/renomeia
            try:
                shutil.move(downloaded_file, final_filename)
                print(f'  ✅ PDF salvo como: {final_filename}')
                return True
            except Exception as e:
                print(f'  ❌ Erro ao salvar PDF: {e}')
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                return False
                
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            # Se é imagem, converte para PDF
            print(f"  🖼️ Convertendo imagem {file_extension} para PDF")
            success = converter_imagem_para_pdf(downloaded_file, plate, userId, final_filename)
            
            # Remove o arquivo temporário de imagem
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
                
            if success:
                print(f'  ✅ PDF gerado a partir da imagem: {final_filename}')
                return True
            else:
                return False
                
        else:
            # Tipo de arquivo não suportado
            print(f"  ⚠️ Tipo de arquivo não suportado: {file_extension}")
            # Cria um PDF de erro
            c = canvas.Canvas(final_filename, pagesize=letter)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, 750, "DOCUMENTO DE HABILITAÇÃO - CNH")
            c.setFont("Helvetica", 12)
            c.drawString(100, 720, f"Placa do Veículo: {plate}")
            c.drawString(100, 700, f"ID do Usuário: {userId}")
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, 650, f"ERRO: Tipo de arquivo não suportado ({file_extension})")
            c.save()
            
            # Remove arquivo temporário
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
                
            print(f"  ⚠️ PDF de aviso criado: {final_filename}")
            return True
        
    except Exception as e:
        print(f"  ❌ [ERRO] Falha ao processar CNH - Usuário: {userId}: {e}")
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass
        return False

def baixar_arquivo_cnh(user_id, bearer_token, filename):
    """Baixa o arquivo da CNH para o usuário específico"""
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {bearer_token}"
    }
    
    url = CNH_URL_TEMPLATE.format(user_id)
    print(url)
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Parse a resposta JSON
        response_data = response.json()
        if response_data.get('dataResult'):
            cnh_url = response_data['dataResult']
            
            # Baixa o arquivo da URL pré-assinada
            temp_file = os.path.join(OUTPUT_DIR, f"temp_{filename}")
            with requests.get(cnh_url, stream=True) as r:
                r.raise_for_status()
                with open(temp_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Arquivo baixado para {filename}")
            return temp_file
    else:
        print(f"Erro ao baixar CNH para user_id {user_id}: {response.status_code}")
        return None

def converter_para_pdf(arquivo_temp, placa, user_id, output_path):
    """Converte o arquivo baixado para PDF (função legada)"""
    try:
        # Verifica se o arquivo é uma imagem
        extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        is_imagem = any(arquivo_temp.lower().endswith(ext) for ext in extensoes_imagem)
        
        # Cria o PDF
        c = canvas.Canvas(output_path, pagesize=letter)
        
        # Adiciona informações no PDF
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "DOCUMENTO DE HABILITAÇÃO - CNH")
        c.setFont("Helvetica", 12)
        c.drawString(100, 720, f"Placa do Veículo: {placa}")
        c.drawString(100, 700, f"ID do Usuário: {user_id}")
        
        if is_imagem:
            # Se for imagem, adiciona informação
            c.drawString(100, 650, "Arquivo de imagem baixado com sucesso.")
            c.drawString(100, 630, "Verifique o arquivo original para visualização da imagem.")
        else:
            # Tenta ler como texto
            try:
                with open(arquivo_temp, 'r', encoding='utf-8') as f:
                    texto = f.read()
                
                c.drawString(100, 650, "Conteúdo do arquivo:")
                c.setFont("Helvetica", 10)
                y_position = 630
                
                for linha in texto.split('\n'):
                    if y_position < 100:  # Nova página se necessário
                        c.showPage()
                        c.setFont("Helvetica", 10)
                        y_position = 750
                    c.drawString(100, y_position, linha[:80])
                    y_position -= 12
            except UnicodeDecodeError:
                c.drawString(100, 650, "Arquivo binário - conteúdo não legível como texto")
        
        c.save()
        print(f"PDF criado: {output_path}")
        
    except Exception as e:
        print(f"Erro ao converter para PDF: {e}")

def processar_boletins():
    """Processa todos os boletins de ocorrência"""
    # Limpa a pasta
    limpar_pasta()
    
    # Obtém o token via Auth
    auth = Auth()
    bearer_token = auth.get_token()
    if not bearer_token:
        print("Falha ao obter token. Abortando...")
        return
    
    # Lê o arquivo Excel
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"Encontrados {len(df)} registros no arquivo Excel: {EXCEL_FILE}")
    except Exception as e:
        print(f"Erro ao ler arquivo Excel: {e}")
        return
    
    # Processa cada linha do Excel usando a nova função
    for index, row in df.iterrows():
        try:
            placa = str(row.get('dataVehiclePlate', '')).strip()
            raw_user = row.get('dataUserId', None)

            # valida user_id
            if pd.isna(raw_user) or str(raw_user).strip() in ('', '-', 'NaN', 'None'):
                print(f"Linha {index}: userId inválido ('{raw_user}'), pulando")
                continue

            # tenta converter de forma segura (aceita floats como '123.0')
            try:
                user_id = str(int(float(raw_user))).strip()
            except Exception:
                cleaned = str(raw_user).strip()
                if cleaned.isdigit():
                    user_id = cleaned
                else:
                    print(f"Linha {index}: userId não conversível ('{raw_user}'), pulando")
                    continue

            print(f"Processando: Placa {placa}, UserID {user_id}")

            # Usa a nova função para processar a CNH
            resultado = process_driver_license(user_id, placa, bearer_token)

            if resultado == "TOKEN_EXPIRED":
                print("Token expirado. Reinicie o processo.")
                break
            # Se resultado for False, não cria nada - a CNH não será incluída no merge
            if not resultado:
                print(f"Aviso: CNH não foi baixada para {placa}_{user_id}")

        except Exception as e:
            print(f"Erro ao processar linha {index}: {e}")
            continue

if __name__ == "__main__":
    print("Iniciando processo de download e conversão de CNHs...")
    processar_boletins()
    print("Processo concluído!")