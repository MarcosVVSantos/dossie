import os
import requests
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import shutil
import json

# Configurações - consumidas do .env
EXCEL_FILE = os.getenv("excelPath", r"C:\Users\Marcos Vinicio\Documents\scripts\dossiev4\dossiev4\src\utils\Relatório BOs.xlsx")
OUTPUT_DIR = os.getenv("boOutputPath", r"C:\Users\Marcos Vinicio\Documents\scripts\dossiev4\dossiev4\src\output\gerador\bo")
LOGIN_URL = os.getenv("loginUrl", "https://sso.mottu.cloud/realms/Internal/protocol/openid-connect/token")
BO_URL_TEMPLATE = os.getenv("boUrlTemplate", "https://operation-backend.mottu.cloud/api/v2/Veiculo/BuscarDetalheVeiculoAnexos/{}/{}")

# Credenciais vindo do .env
username = os.getenv('email', 'marcos.santos@mottu.com.br')
password = os.getenv('password', 'mitu.2809')
client_id = os.getenv('client_id', 'mottu-admin')
grant_type = os.getenv('grant_type', 'password')

def limpar_pasta():
    """Limpa a pasta de output antes de executar"""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Pasta {OUTPUT_DIR} limpa e criada")

def obter_token():
    """Obtém o token de autenticação Bearer"""
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    authData = {
        'username': username,
        'password': password,
        'client_id': client_id,
        'grant_type': grant_type
    }
    try:
        authResponse = requests.post(LOGIN_URL, headers=headers, data=authData)
        print(LOGIN_URL)
        print(headers)
        print(authData)

        if authResponse.status_code == 200:
            authToken = authResponse.json().get('access_token')
            return authToken
        else:
            print(f'Erro na autenticação: {authResponse.status_code}')
            return None
    except Exception as e:
        print(f'Erro na requisição de autenticação: {e}')
        return None

def download_bo_file(url, local_filename):
    """Faz o download do arquivo do BO usando URL pré-assinada"""
    try:
        print(f"  📥 Baixando BO de URL pré-assinada: {url}")
        
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
        print(f"  ❌ Erro ao baixar arquivo do BO: {e}")
        return None

def get_bo_data(vehicle_id, bo_type, token):
    """Obtém os dados do BO da API"""
    try:
        headers = {
            "accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {token}",
            "Language": "pt-BR",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Referer": "https://admin-v3.mottu.cloud/"
        }
        
        url = BO_URL_TEMPLATE.format(vehicle_id, bo_type)
        print(f"  🔍 Buscando dados do BO: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Parse a resposta JSON
            response_data = response.json()
            print(f"  ✅ Dados do BO encontrados")
            return response_data
        elif response.status_code == 401:
            print("  🔐 Token expirado")
            return "TOKEN_EXPIRED"
        elif response.status_code == 404:
            print(f"  ⚠️ BO não encontrado para veículo {vehicle_id}, tipo {bo_type}")
            return None
        else:
            print(f"  ❌ Erro ao buscar dados do BO: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Erro na requisição dos dados do BO: {e}")
        return None

def extrair_url_anexo(bo_data):
    """Extrai a URL do anexo dos dados do BO"""
    try:
        print(f"  🔍 Analisando estrutura dos dados do BO...")
        
        # Função recursiva para buscar URLs
        def buscar_url(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, str) and value.startswith('http'):
                        print(f"  ✅ URL encontrada em {current_path}: {value}")
                        return value
                    elif isinstance(value, (dict, list)):
                        result = buscar_url(value, current_path)
                        if result:
                            return result
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    result = buscar_url(item, current_path)
                    if result:
                        return result
            return None
        
        url = buscar_url(bo_data)
        
        if not url:
            print("  ⚠️ Nenhuma URL de anexo encontrada nos dados do BO")
            print(f"  Estrutura disponível: {json.dumps(bo_data, indent=2)[:500]}...")
        
        return url
        
    except Exception as e:
        print(f"  ❌ Erro ao extrair URL do anexo: {e}")
        return None

def obter_url_pre_assinada(url_original, token):
    """Obtém uma URL pré-assinada atualizada para o arquivo"""
    try:
        # Se a URL já é uma URL pré-assinada do S3, tentamos obter uma nova
        if 's3.amazonaws.com' in url_original and 'AWSAccessKeyId' in url_original:
            print("  🔄 URL pré-assinada expirada detectada, tentando obter nova...")
            
            # Extrai o caminho do arquivo do S3 da URL original
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url_original)
            s3_path = parsed.path.lstrip('/')
            
            # Aqui precisaríamos de um endpoint específico para gerar nova URL pré-assinada
            # Como não temos, vamos tentar usar a URL diretamente ou buscar alternativa
            print("  ⚠️ Não foi possível renovar URL pré-assinada automaticamente")
            return None
        
        # Se não é URL do S3 ou já é uma URL válida, retorna a original
        return url_original
        
    except Exception as e:
        print(f"  ❌ Erro ao obter URL pré-assinada: {e}")
        return None

def converter_imagem_para_pdf(arquivo_imagem, placa, vehicle_id, bo_type, output_pdf):
    """Converte arquivo de imagem (JPG, PNG) para PDF"""
    try:
        # Cria o PDF
        c = canvas.Canvas(output_pdf, pagesize=letter)
        
        # Adiciona informações no PDF
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "BOLETIM DE OCORRÊNCIA")
        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Placa do Veículo: {placa}")
        c.drawString(100, 710, f"ID do Veículo: {vehicle_id}")
        c.drawString(100, 690, f"Tipo do BO: {bo_type}")
        c.drawString(100, 670, f"Data de processamento: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Adiciona a imagem ao PDF
        try:
            # Lê a imagem
            img = ImageReader(arquivo_imagem)
            img_width, img_height = img.getSize()
            
            # Calcula o tamanho para caber na página mantendo a proporção
            page_width = 500
            page_height = 600
            x_position = 50
            y_position = 50
            
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
            c.drawString(100, 650, "Erro ao processar a imagem do BO")
            c.drawString(100, 630, "Arquivo de imagem disponível na pasta")
        
        c.save()
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao converter imagem para PDF: {e}")
        return False

def process_bo(vehicle_id, bo_type, placa, token):
    """Processa o BO do veículo: busca dados, extrai URL e baixa arquivo"""
    try:
        vehicle_id = int(vehicle_id)
        bo_type = int(bo_type)
        placa = str(placa).strip().upper()
        
        print(f"  🔍 Buscando BO para Veículo: {vehicle_id}, Tipo: {bo_type}, Placa: {placa}")
        
        # Buscar dados do BO
        bo_data = get_bo_data(vehicle_id, bo_type, token)
        
        if bo_data == "TOKEN_EXPIRED":
            return "TOKEN_EXPIRED"
        
        if not bo_data:
            print(f"  ⚠️ Nenhum BO encontrado para o veículo {vehicle_id}")
            return True
        
        # Extrair URL do anexo
        anexo_url = extrair_url_anexo(bo_data)
        
        if not anexo_url:
            print(f"  ⚠️ Nenhum anexo encontrado para o BO do veículo {vehicle_id}")
            # Cria um PDF com os dados disponíveis
            return criar_pdf_com_dados_bo(bo_data, placa, vehicle_id, bo_type)
        
        # Verificar se a URL precisa de renovação
        anexo_url_atualizada = obter_url_pre_assinada(anexo_url, token)
        if anexo_url_atualizada:
            anexo_url = anexo_url_atualizada
        
        # Nome do arquivo temporário
        temp_filename = os.path.join(OUTPUT_DIR, f"temp_bo_{vehicle_id}_{bo_type}")
        
        # Fazer download do arquivo usando URL pré-assinada
        print(f"  📥 Baixando anexo do BO")
        downloaded_file = download_bo_file(anexo_url, temp_filename)
        
        if not downloaded_file:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            # Cria um PDF com os dados disponíveis mesmo com falha no download
            return criar_pdf_com_dados_bo(bo_data, placa, vehicle_id, bo_type)
        
        # Verifica o tipo de arquivo baixado
        file_extension = os.path.splitext(downloaded_file)[1].lower()
        
        # Caminho final do arquivo
        final_filename = os.path.join(OUTPUT_DIR, f"{placa}_{vehicle_id}_BO_{bo_type}.pdf")
        
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
                return criar_pdf_com_dados_bo(bo_data, placa, vehicle_id, bo_type)
                
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            # Se é imagem, converte para PDF
            print(f"  🖼️ Convertendo imagem {file_extension} para PDF")
            success = converter_imagem_para_pdf(downloaded_file, placa, vehicle_id, bo_type, final_filename)
            
            # Remove o arquivo temporário de imagem
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
                
            if success:
                print(f'  ✅ PDF gerado a partir da imagem: {final_filename}')
                return True
            else:
                return criar_pdf_com_dados_bo(bo_data, placa, vehicle_id, bo_type)
                
        else:
            # Tipo de arquivo não suportado
            print(f"  ⚠️ Tipo de arquivo não suportado: {file_extension}")
            return criar_pdf_com_dados_bo(bo_data, placa, vehicle_id, bo_type, file_extension)
        
    except Exception as e:
        print(f"  ❌ [ERRO] Falha ao processar BO - Veículo: {vehicle_id}: {e}")
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass
        return False

def criar_pdf_com_dados_bo(bo_data, placa, vehicle_id, bo_type, file_extension=None):
    """Cria um PDF com os dados do BO quando não é possível baixar o anexo"""
    try:
        final_filename = os.path.join(OUTPUT_DIR, f"{placa}_{vehicle_id}_BO_{bo_type}.pdf")
        
        c = canvas.Canvas(final_filename, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "BOLETIM DE OCORRÊNCIA - DADOS DISPONÍVEIS")
        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Placa do Veículo: {placa}")
        c.drawString(100, 710, f"ID do Veículo: {vehicle_id}")
        c.drawString(100, 690, f"Tipo do BO: {bo_type}")
        c.drawString(100, 670, f"Data de processamento: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        if file_extension:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, 640, f"Arquivo em formato não suportado: {file_extension}")
        
        c.setFont("Helvetica", 10)
        y_position = 620
        c.drawString(100, y_position, "Dados do BO disponíveis:")
        y_position -= 20
        
        # Converte dados do BO para string formatada
        try:
            bo_info = json.dumps(bo_data, indent=2, ensure_ascii=False)
            for linha in bo_info.split('\n'):
                if y_position < 100:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = 750
                c.drawString(100, y_position, linha[:80])
                y_position -= 12
        except Exception as e:
            c.drawString(100, y_position, f"Não foi possível exibir os dados do BO: {e}")
        
        c.save()
        print(f"  📄 PDF com dados do BO criado: {final_filename}")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao criar PDF com dados do BO: {e}")
        return False

def processar_boletins():
    """Processa todos os boletins de ocorrência"""
    # Limpa a pasta
    limpar_pasta()
    
    # Obtém o token
    bearer_token = obter_token()
    if not bearer_token:
        print("Falha ao obter token. Abortando...")
        return
    
    # Lê o arquivo Excel
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"Encontrados {len(df)} registros no arquivo Excel")
        
        # Verifica se as colunas necessárias existem
        required_columns = ['dataVehiclePlate', 'dataVehicleId', 'dataOccurrenceType']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ Colunas faltando no Excel: {missing_columns}")
            return
            
    except Exception as e:
        print(f"Erro ao ler arquivo Excel: {e}")
        return
    
    # MAPEAMENTO: dataOccurrenceType -> bo_type
    # Apenas processa quando dataOccurrenceType = 10, usando bo_type = 3
    ocorrencia_para_bo = {
        10: "3"  # dataOccurrenceType 10 -> bo_type 3
        # Adicione outros mapeamentos conforme necessário:
        # 5: "5",  # dataOccurrenceType 5 -> bo_type 5
        # 8: "2",  # dataOccurrenceType 8 -> bo_type 2
    }
    
    # Processa cada linha do Excel
    for index, row in df.iterrows():
        try:
            placa = str(row['dataVehiclePlate']).strip()
            vehicle_id = str(int(row['dataVehicleId'])).strip()
            data_occurrence_type = int(row['dataOccurrenceType'])
            
            # Verifica se este dataOccurrenceType deve ser processado
            if data_occurrence_type in ocorrencia_para_bo:
                bo_type = ocorrencia_para_bo[data_occurrence_type]
                
                print(f"\n📋 Processando linha {index + 1}: Placa {placa}, VehicleID {vehicle_id}, DataOccurrenceType {data_occurrence_type}, TipoBO {bo_type}")
                
                # Usa a função para processar o BO
                resultado = process_bo(vehicle_id, bo_type, placa, bearer_token)
                
                if resultado == "TOKEN_EXPIRED":
                    print("🔐 Token expirado. Reinicie o processo.")
                    break
                elif not resultado:
                    print(f"❌ Falha ao processar BO para veículo {vehicle_id}")
            else:
                print(f"⏭️  Pulando linha {index + 1}: dataOccurrenceType {data_occurrence_type} não está no mapeamento")
                
        except Exception as e:
            print(f"❌ Erro ao processar linha {index}: {e}")
            continue

if __name__ == "__main__":
    print("🚀 Iniciando processo de download e conversão de Boletins de Ocorrência...")
    processar_boletins()
    print("✅ Processo concluído!")