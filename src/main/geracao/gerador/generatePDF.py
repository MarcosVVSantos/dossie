import os
import sys
import time
import requests
import pandas as pd
import unicodedata
from fpdf import FPDF
from datetime import datetime
from requests.structures import CaseInsensitiveDict
from PIL import Image
from datetime import datetime
import math
from pathlib import Path

# Garante que o pacote src seja encontrado quando rodar o script direto
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.settings.config import config
from src.settings.auth import Auth

# Configurações via Config
GEOPYFY_URL = os.getenv("geopifyUrl", "https://api.geoapify.com/v1/geocode/")
GEOPYFY_KEY = os.getenv("geopify", "")

# Caminho correto para a pasta document
project_root_for_output = Path(__file__).resolve().parents[4]
saidaPath = str(project_root_for_output / "src" / "output" / "gerador" / "document")
logoPath = os.getenv('logoPath') or os.getenv('logo') or str(project_root_for_output / "src" / "utils" / "logo.png")

# Auth helper
_auth = Auth()

def auth_token():
    """Obtém token usando Auth (cached)"""
    return _auth.get_token()

# Garantir que o diretório de saída existe
os.makedirs(saidaPath, exist_ok=True)

# Dados da Mottu (valores do .env com fallback)
MOTTU_CNPJ = os.getenv("MOTTU_CNPJ", "17.182.260/0001-08")
MOTTU_ADDRESS = os.getenv("MOTTU_ADDRESS", "Av. Dr. Gastão Vidigal, 501 - Vila Leopoldina, São Paulo - SP, 05314-000")
MOTTU_PHONE = os.getenv("MOTTU_PHONE", "(11) 3181-8188")

# Caminho do Excel (valor do .env com fallback)
EXCEL_PATH = os.getenv("excelPath", r"C:\Users\Marcos Vinicio\Documents\scripts\dossiev4\dossiev4\src\utils\Relatório BOs.xlsx")

# Função para limpar a pasta document (mantida a implementação existente)
def limpar_pasta_document():
    """
    Limpa a pasta document antes de iniciar o processamento
    """
    try:
        if os.path.exists(saidaPath):
            for filename in os.listdir(saidaPath):
                file_path = os.path.join(saidaPath, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"Arquivo removido: {file_path}")
                except Exception as e:
                    print(f"Erro ao remover {file_path}: {e}")
            print(f"Pasta document limpa com sucesso: {saidaPath}")
        else:
            print(f"Pasta document não existe, criando: {saidaPath}")
            os.makedirs(saidaPath, exist_ok=True)
    except Exception as e:
        print(f"Erro ao limpar pasta document: {e}")

class PDFGenerator:
    """Implementação atualizada para replicar o layout do documento fornecido."""
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or saidaPath
        os.makedirs(self.output_dir, exist_ok=True)
        # CONSTANTES DE FONTE - VALORES REDUZIDOS
        self.FONT_SIZE_LARGE = 12    # Para títulos muito importantes
        self.FONT_SIZE_TITLE = 10    # Era 16 - REDUZIDO
        self.FONT_SIZE_SUBTITLE = 9  # Era 12 - REDUZIDO  
        self.FONT_SIZE_NORMAL = 8    # Era 10 - REDUZIDO
        self.FONT_SIZE_SMALL = 7     # Era 9 - REDUZIDO

    def generate_document_pdf(self, replacements, plate, doc_type_name, branch_id, user_id):
        try:
            filename = f"{plate}_{user_id}.pdf"
            out_path = os.path.join(self.output_dir, filename)

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # PRIMEIRA PÁGINA - BOLETIM DE OCORRÊNCIA
            pdf.add_page()
            
            # Logo centralizado e maior
            logo_height = 0
            try:
                if os.path.exists(logoPath):
                    logo_width = 50
                    page_width = pdf.w
                    x_position = (page_width - logo_width) / 2
                    pdf.image(logoPath, x=x_position, y=15, w=logo_width)
                    logo_height = 25
            except Exception:
                pass
            
            # Título principal centralizado (CORRIGIDO: não sobrepõe o logo)
            pdf.set_y(15 + logo_height)
            pdf.set_font("Arial", 'B', self.FONT_SIZE_TITLE)
            pdf.cell(0, 8, doc_type_name, ln=True, align='C')
            pdf.ln(3)
            
            # Empresa requerente
            pdf.set_font("Arial", size=self.FONT_SIZE_NORMAL)
            empresa_texto = f"A empresa {replacements.get('RAZAO_MOTTU', 'MOTTU III S.A.')}, CNPJ {MOTTU_CNPJ}, com sede {MOTTU_ADDRESS}, vem requerer registro de boletim de ocorrência pelos motivos a seguir expostos:"
            pdf.multi_cell(0, 4, empresa_texto)
            pdf.ln(5)
            
            # DADOS DA OCORRÊNCIA
            pdf.set_font("Arial", 'B', self.FONT_SIZE_SUBTITLE)
            pdf.cell(0, 6, "DADOS DA OCORRÊNCIA:", ln=True)
            pdf.set_font("Arial", size=self.FONT_SIZE_NORMAL)
            
            dados_ocorrencia = [
                f"LOCAL DO FATO: {replacements.get('LOCAL DO FATO: ENDERECO_OCORRENCIA', 'Endereço não disponível')}",
                f"DATA DO FATO: {replacements.get('DATA_OCORRENCIA', 'Data não disponível')}",
                f"HORA DO FATO: {replacements.get('HORA_OCORRENCIA', 'Hora não disponível')}"
            ]
            
            for linha in dados_ocorrencia:
                pdf.cell(0, 4, linha, ln=True)
            
            pdf.ln(3)
            
            # VÍTIMA / LOCATÁRIO
            pdf.set_font("Arial", 'B', self.FONT_SIZE_SUBTITLE)
            pdf.cell(0, 6, "VÍTIMA / LOCATÁRIO:", ln=True)
            pdf.set_font("Arial", size=self.FONT_SIZE_NORMAL)
            
            vitima_texto = [
                f"VÍTIMA (Empresa): {replacements.get('RAZAO_MOTTU', 'MOTTU III S.A.')}, CNPJ: {MOTTU_CNPJ}, Endereço: {MOTTU_ADDRESS}, Telefone: {MOTTU_PHONE}",
                f"LOCATÁRIO: {replacements.get('NOME_LOCAT', 'Nome não disponível')}, CPF: {replacements.get('CPF_LOCAT', 'CPF não disponível')}, Endereço: {replacements.get('ENDERECO_LOCAT', 'Endereço não disponível')}"
            ]
            
            for linha in vitima_texto:
                pdf.multi_cell(0, 4, linha)
                pdf.ln(1)
            
            pdf.ln(3)
            
            # DADOS DO VEÍCULO
            pdf.set_font("Arial", 'B', self.FONT_SIZE_SUBTITLE)
            pdf.cell(0, 6, "DADOS DO VEÍCULO:", ln=True)
            pdf.set_font("Arial", size=self.FONT_SIZE_NORMAL)
            pdf.cell(0, 4, f"Modelo: {replacements.get('MARCA_MODELO', 'Modelo não disponível')}, Placa: {plate}, CNPJ Proprietário: {MOTTU_CNPJ}", ln=True)
            
            pdf.ln(5)
            
            # HISTÓRICO
            pdf.set_font("Arial", 'B', self.FONT_SIZE_SUBTITLE)
            pdf.cell(0, 6, "HISTÓRICO:", ln=True)
            pdf.set_font("Arial", size=self.FONT_SIZE_NORMAL)
            
            texto_historico = replacements.get('TEXTO', 'Histórico não disponível')
            pdf.multi_cell(0, 4, texto_historico)
            
            pdf.ln(8)
            
            # Data e local da assinatura
            data_atual = datetime.now().strftime("%d/%m/%Y")
            pdf.cell(0, 4, f"São Paulo - SP, {data_atual}.", ln=True, align='R')
            
            # Continue ajustando as demais páginas com as mesmas constantes de fonte...
            
            # Para as outras páginas, use:
            # pdf.set_font("Arial", 'B', self.FONT_SIZE_TITLE) para títulos
            # pdf.set_font("Arial", size=self.FONT_SIZE_NORMAL) para texto normal
            # pdf.set_font("Arial", size=self.FONT_SIZE_SMALL) para texto pequeno

            pdf.output(out_path)
            return out_path
        except Exception as e:
            print(f"Erro gerando PDF: {e}")
            return None
        
# ... (o restante do código permanece exatamente igual) ...
def get_cpf_from_api(user_id, token):
    headers = {
        "accept": "text/plain",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json-patch+json"
    }
    try:
        uid = str(user_id).strip()
        if uid in ('', '-', 'None', 'NaN'):
            return 'CPF não encontrado'
        # tenta normalizar para inteiro quando aplicável
        try:
            uid_int = int(float(uid))
        except Exception:
            uid_int = uid
        url = f'https://user-management.mottu.cloud/v1/users?Code={uid_int}'
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            return resp.json().get('result', {}).get('individualRegistration', 'CPF não encontrado')
        return 'CPF não encontrado'
    except Exception:
        return 'CPF não encontrado'

def format_date(dates_list):
    """
    Recebe lista de datas (pandas Series -> .tolist()) e retorna duas listas:
    [dd/mm/YYYY], [HH:MM]. Trata valores nulos/invalidos.
    """
    formatted_dates = []
    formatted_hours = []
    for v in dates_list:
        try:
            if v is None or (isinstance(v, float) and math.isnan(v)) or str(v).strip() in ('', '-', 'NaT'):
                formatted_dates.append("Data não disponível")
                formatted_hours.append("Hora não disponível")
                continue
            dt = pd.to_datetime(v, errors='coerce')
            if pd.isna(dt):
                formatted_dates.append("Data não disponível")
                formatted_hours.append("Hora não disponível")
            else:
                formatted_dates.append(dt.strftime("%d/%m/%Y"))
                formatted_hours.append(dt.strftime("%H:%M"))
        except Exception:
            formatted_dates.append("Data não disponível")
            formatted_hours.append("Hora não disponível")
    return formatted_dates, formatted_hours

def geopify_search(lat, lon):
    """Consulta Geoapify (se chave presente) ou retorna 'lat, lon' como fallback."""
    try:
        if not GEOPYFY_KEY:
            return f"{lat}, {lon}"
        url = GEOPYFY_URL.rstrip('/') + "/reverse"
        params = {"lat": lat, "lon": lon, "apiKey": GEOPYFY_KEY}
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        # melhora: pega first feature properties.formatted
        features = data.get('features') or []
        if features:
            props = features[0].get('properties', {})
            return props.get('formatted', f"{lat}, {lon}")
        return f"{lat}, {lon}"
    except Exception:
        return f"{lat}, {lon}"

def format_cnpj(val):
    """Formato simples para CNPJ (fallback)."""
    s = ''.join(ch for ch in str(val) if ch.isdigit())
    if len(s) == 14:
        return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"
    return str(val)

def format_cellphone(val):
    """Formato simples para telefone (fallback)."""
    s = ''.join(ch for ch in str(val) if ch.isdigit())
    if len(s) == 11:
        return f"({s[:2]}) {s[2:7]}-{s[7:]}"
    if len(s) == 10:
        return f"({s[:2]}) {s[2:6]}-{s[6:]}"
    return str(val)

def main():
    """Função principal"""
    print("🚀 Iniciando geração de Boletins de Ocorrência...")
    
    # Limpar a pasta document antes de iniciar
    print("🧹 Limpando pasta document...")
    limpar_pasta_document()
    
    # Obter token de autenticação
    print("🔑 Obtendo token de autenticação...")
    token = auth_token()
    if not token:
        print("❌ Erro ao obter token de autenticação")
        return
    print("✅ Token obtido com sucesso!")
    
    # Verificar se o logo existe
    if not os.path.exists(logoPath):
        print(f"⚠️ Aviso: Logo não encontrada em {logoPath}")
        print("📄 Os PDFs serão gerados sem o logo.")
    
    # Carregar dados do Excel
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name='Página1')
        print(f"📊 Excel carregado: {len(df)} registros encontrados")
        
        print("📋 Colunas disponíveis:", df.columns.tolist())
        
    except Exception as e:
        print(f"❌ Erro ao carregar Excel: {e}")
        return

    # Remover duplicatas para não gerar o mesmo PDF mais de uma vez
    def _normalize_user(val):
        try:
            s = str(val).strip()
            if s in ('', '-', 'None', 'NaN'):
                return ''
            return str(int(float(s)))
        except Exception:
            return str(val).strip()

    if 'dataVehiclePlate' in df.columns and 'dataUserId' in df.columns:
        df['dataVehiclePlate'] = df['dataVehiclePlate'].astype(str).str.strip().str.upper()
        df['__user_norm__'] = df['dataUserId'].apply(_normalize_user)

        before = len(df)
        df = df.drop_duplicates(subset=['dataVehiclePlate', '__user_norm__'])
        after = len(df)
        if after < before:
            print(f"🔁 Linhas duplicadas removidas: {before - after}")

        df['dataUserId'] = df['__user_norm__']
        df = df.drop(columns=['__user_norm__']).reset_index(drop=True)

    # Inicializar gerador de PDF
    pdf_generator = PDFGenerator()
    
    # Arrays para armazenar dados processados
    data_user_full_name = []
    data_user_rg = []
    data_user_cpf = []
    data_user_phone = []
    data_user_address = []
    data_address = []
    data_tracking_address = []
    
    # Processar dados dos usuários
    for i, row in df.iterrows():
        data_user_full_name.append(row.get('dataNameUser', 'Nome não disponível'))
        data_user_rg.append("RG não disponível")
        data_user_phone.append("Telefone não disponível")
        data_user_address.append(row.get('dataBranchAddress', 'Endereço não disponível'))
        
        # Buscar CPF via API
        user_id = row.get('dataUserId')
        if pd.notna(user_id):
            try:
                print(f"🔍 Buscando CPF para usuário ID: {user_id}")
                cpf = get_cpf_from_api(user_id, token)
                data_user_cpf.append(cpf)
                print(f"📋 CPF obtido: {cpf}")
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Erro ao buscar CPF para usuário {user_id}: {e}")
                data_user_cpf.append("CPF não encontrado")
        else:
            data_user_cpf.append("ID não disponível")
    
    # Processar endereços das ocorrências
    for coord in df['dataOccurenceAddress']:
        if isinstance(coord, str) and ',' in coord:
            try:
                lat, lon = map(float, coord.replace(' ', '').split(','))
                address = geopify_search(lat, lon)
                data_address.append(address)
            except:
                data_address.append(str(coord))
        else:
            data_address.append(str(coord))
    
    # Processar endereços de tracking
    for coord in df['dataTrackingGeolocation']:
        if isinstance(coord, str) and ',' in coord:
            try:
                lat, lon = map(float, coord.replace(' ', '').split(','))
                address = geopify_search(lat, lon)
                data_tracking_address.append(address)
            except:
                data_tracking_address.append(str(coord))
        else:
            data_tracking_address.append(str(coord))
    
    # Formatar datas
    occurrence_dates, occurrence_hours = format_date(df['dataOccurenceDate'].tolist())
    tracking_dates, tracking_hours = format_date(df['dataTrackingDate'].tolist())
    
    # Formatar CNPJ
    cnpj_formatted = [format_cnpj(cnpj) for cnpj in df['dataBranchId']]
    
    # Formatar telefones
    user_phones = [format_cellphone(phone) for phone in data_user_phone]
    
    # Gerar textos para cada tipo de ocorrência (BASEADO NO DOCUMENTO FORNECIDO)
    texts = []
    for i, row in df.iterrows():
        occurrence_type = int(row['dataOccurrenceType'])
        plate = row['dataVehiclePlate']
        model = row['dataVehicleModel']
        user_name = data_user_full_name[i] if i < len(data_user_full_name) else 'Nome não disponível'
        user_cpf = data_user_cpf[i] if i < len(data_user_cpf) else 'CPF não disponível'
        
        if occurrence_type == 1:  # ROUBO
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, o locatario {user_name}, portador do RG {data_user_rg[i]},'
                f'notificou através do aplicativo que a motocicleta de modelo {model} e placa {plate}, foi comunicada como roubada no endereço'
                f'{data_address[i]}. Apos o incidente, o GPS do veiculo deixou de transmitir sinais. O gps do veiculo deixou'
                f'de transmitir sinails. O cliente entrou em contato inicialmente pelo aplicativo para relatar o ocorrido. '
                f'Apesar das dilegências, realizadas para a recuperação do veiculo, não foi possivel alcançar êxito nas operações. '
                f'O ultimo sinal de GPS foi registrado em {tracking_dates[i]} às {tracking_hours[i]} UTC, na endereço {data_tracking_address[i]}.'
            )
            
        elif occurrence_type == 2:  # INVENTARIO
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, durante a realização do inventario, foi constatado que a motocicleta,'
                f'de modelo {model} e placa {plate}, não se encontrava mais nas instalações da Mottu '
                f'localizada no endereço {data_user_address[i]}, e não há mais registros da sua localização através do rastreador '
                f'O ultimo sinal de GPS foi registrado em {tracking_dates[i]} às {tracking_hours[i]} UTC, no endereço {data_tracking_address[i]}.'
            )
            
        elif occurrence_type == 3:  # FURTO
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, o locatario {user_name}, portador do RG {data_user_rg[i]}, '
                f'notificou através do aplicativo que a motocicleta de modelo {model} e placa {plate}, foi comunicada como furtada '
                f'no endereço {data_address[i]}. Apos o incidente, o GPS do veiculo deixou de transmitir sinais. O gps do veiculo '
                f'deixou de transmitir sinais. O cliente entrou em contato inicialmente pelo aplicativo para relatar o ocorrido. '
                f'Apesar das dilegências, realizadas para a recuperação do veiculo, não foi possivel alcançar êxito nas operações. '
                f'O ultimo sinal de GPS foi registrado em {tracking_dates[i]} às {tracking_hours[i]} UTC, na endereço {data_tracking_address[i]}.'
            )
            
        elif occurrence_type == 4:  # VIOLAÇÃO
            texts.append(
                f'A Sra. Solange Brolezo, RG: 16.505.649-6, CPF: 094.377.888-39, residente na Rua Altamiro de Souza Bueno, 417, JD Bela Vista Joanópolis - SP, '
                f'Telefone: (11) 96904-7320, representante das empresas locadoras de moto denominadas Mottu Locação de Veículos, Mottu I S/A, Mottu II S/A, '
                f'Mottu III S/A, Mottu IV S/A, Mottu V S/A, Mottu VI S/A, Mottu VII S.A, Mottu Natal e Mottu Brasília através do presente documento informa que '
                f'o motociclo acima descrito foi furtado na data e hora acima informadas no endereço declarado como local do fato. '
                f'Foram adotadas diligências para localização e recuperação do bem, porém sem êxito até o momento. '
                f'O último sinal de GPS foi captado em {tracking_dates[i]}, às {tracking_hours[i]} UTC, com geolocalização correspondente ao endereço {data_tracking_address[i]}.'
            )
            
        elif occurrence_type == 5:  # APROPRIAÇÃO INDÉBITA
            texts.append(
                f'No dia {occurrence_dates[i]} foi encerrado o contrato de locação celebrado com {user_name}, portador do RG {data_user_rg[i]}, '
                f'referente à motocicleta de modelo {model} e placa {plate}. '
                f'A partir deste momento, o veiculo deixou de ser localizado, passando a ser deliberadamente ocultado pelo '
                f'ex-locatario. Todas as tentativas de contato foram ignoradas, não sendo possivel qualquer forma '
                f'de recuperação do bem. O rastreador foi desativado e o ultimo sinal de GPS foi registrado em '
                f'{tracking_dates[i]} às {tracking_hours[i]} UTC, no endereço {data_tracking_address[i]}. '
                f'Desde então, a motocicleta encontra-se em local ignorado, fora do alcance da empresa, sem qualquer devolutiva por parte do ex-locatario. '
                f'O conjunto dos fatos, apontam para uma conduta que extrapola a mera inadimplencia contratual, configurando '
                f'evidente subtração do veiculo, que permanece fora da posse da legitima proprietaria.'
            )
            
        elif occurrence_type == 6:  # VEICULO ENCONTRADO
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, o rastreador do veiculo voltou a emitir sinais com a sua localização nas coordenadas: ({row["dataTrackingGeolocation"]}). '
                f'Deste modo, para averiguação dos sinais transmitidos foi enviado um prestador ao local. O motorista {row.get("dataOccurrenceBranchDriverName", "Motorista não informado")} foi designado  '
                f'para a tarefa. Ao chegar ao local, confirmou a presença do veiculo da placa: {plate.upper()}, e chassi: {row.get("dataVehicleChassis", "Chassi não informado").upper()}, '
                f'abandonado e procedeu com a sua recolha. O veiculo foi encaminhado para o pátio da empresa para as devidas providências legais e contato.'
            )
            
        elif occurrence_type == 7:  # VEICULO RECUPERADO POR DENUNCIA ANONIMA
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, recebemos uma denúncia por volta das {occurrence_hours[i]}, informando que uma moto de modelo {model.upper()}, '
                f'e placa {plate.upper()}, estava abandonada na localização das coordenadas: ({row["dataTrackingGeolocation"]}). '
                f'Para averiguação da denúncia, foi enviado um prestador ao local. O motorista: {row.get("dataOccurrenceBranchDriverName", "Motorista não informado")} foi designado para a tarefa. '
                f'Ao chegar ao local, onde foi confirmada a presença do veículo da {plate.upper()}, e chassi: {row.get("dataVehicleChassis", "Chassi não informado").upper()}, abandonado e procedeu com a sua recolha. '
                f'O veículo foi encaminhado para o pátio da empresa para as devidas providências legais e contato.'
            )
            
        elif occurrence_type == 8:  # VEICULO APREENDIDO
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, recebemos uma denúncia anônima informando que uma motocicleta de modelo {model.upper()}, '
                f'e placa {plate.upper()}, havia sido apreendida no endereço {data_address[i]}. '
                f'Para averiguação da denúncia, foi enviado um prestador ao local. O motorista: {row.get("dataOccurrenceBranchDriverName", "Motorista não informado")} foi designado para a tarefa. '
                f'Ao chegar no local, foi confirmado a presença do veiculo citado, apos a liberação do veiculo a restrição contida no mesmo ainda continua ativa em sistema, '
                f'Por meio deste documento solicitamos a remoção da restrição do veiculo, uma vez que apos a apreensão foram tomadas as devidas providências legais e contato. '
                f'O veiculo foi encaminhado para o pátio e atualmente encontra-se sob a guarda da empresa, aguardando a regularização de sua situação.'
            )
            
        elif occurrence_type == 9:  # VEICULO APREENDIDO -padrao
            texts.append(
                f'Na data {occurrence_dates[i]} recebemos a informação de que a motocicleta de placa {plate}, modelo {model} e chassi {row.get("dataVehicleChassis", "Chassi não informado")}, '
                f'foi apreendida e encontra-se em pátio. Ressaltamos que, conforme orientação passada pelo orgão responsável, a liberação do veículo não poderá ser efetuada '
                f'enquanto o boletim de ocorrência estiver ativo. Portanto, faz-se necessária a baixa do referido boletim para que o procedimento de liberação do veículo possa ser realizado.'
            )
            
        elif occurrence_type == 10:  # ALTERAÇÃO ROUBO/FURTO (formato específico)
            occ_date = occurrence_dates[i] if i < len(occurrence_dates) else "Data não disponível"
            loc_name = user_name if user_name else "Nome não disponível"
            # tenta extrair somente dígitos do CPF; senão mostra o que vier
            cpf_digits = ''.join(ch for ch in (user_cpf or "") if ch.isdigit())
            loc_cpf_display = cpf_digits if cpf_digits else (user_cpf or "CPF não disponível")
            model_display = (model or "Modelo não disponível")
            plate_display = (plate or "PLACA NÃO DISPONÍVEL")

            texts.append(
                f"Compareceu a esta Unidade Policial, a Sra. Solange Brolezo, RG: 16.505.649-6, CPF: 094.377.888-39, residente na Rua Altamiro de\n"
                f"Souza Bueno, 417, JD Bela Vista Joanopolis - SP, Telefone: (11) 96904-7320, representante das empresas locadoras de moto\n"
                f"denominadas Mottu Locacao de Veiculos, Mottu I S/A, Mottu II S/A, Mottu III S/A, Mottu IV S/A, Mottu V S/A, Mottu VI S/A, Mottu VII\n"
                f"S.A e MOTTU Natal S/A, declarando que no dia {occ_date} a empresa locadora cadastrada como vitima, conseguiu contato com o\n"
                f"locatario {loc_name} (CPF: {loc_cpf_display}), locatario do motociclo {model_display} placa {plate_display}, tendo\n"
                f"ele informado que nao devolveu o motociclo locado em virtude do mesmo ter sido furtado, conforme descrito na documentacao ora\n"
                f"apresentada e que nao conseguiu comunicar a empresa/vitima sobre o ocorrido, gerando assim o equivoco quanto a natureza dos\n"
                f"fatos. O representante esclareceu ainda que a empresa/vitima tem realizado levantamentos dos boletins de ocorrencia registrados por\n"
                f"apropriacao indebita, tentando novo contato com os locatarios e em alguns casos tem sido apurado que o ocorrido na verdade\n"
                f"tratou-se de furto, tal como o presente registro. Face a isso, o representante da empresa/vitima solicita que o veiculo mencionado\n"
                f"neste registro seja cadastrado nesta edicao como FURTADO, motivo pelo qual esta edicao e lavrada para fins de alterar o bloqueio de\n"
                f"apropriacao indebita para bloqueio de furto junto ao CEPOL."
            )

        elif occurrence_type ==11:  # FALTA_DE_MOTOR_SPORT
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, durante a realização do inventário, foi '
                f'constatado que o motociclo de modelo {model} e placa {plate}, encontrava-se nas instalações da Mottu '
                f'localizada no endereço {data_user_address[i]}, porém sem o motor. Até o presente momento,  não há informações'
                f' precisas acerca da localização do referido componente.'
            )

        elif occurrence_type == 12:  # VEICULO ENCONTRADO SEM LOCACAO
            texts.append(
                f'No dia {occurrence_dates[i]} e hora {occurrence_hours[i]}, o rastreador do veiculo voltou a emitir sinais com a sua localização nas coordenadas: ({row["dataTrackingGeolocation"]}). '
                f'Deste modo, para averiguação dos sinais transmitidos foi enviado um prestador ao local. O motorista {row.get("dataOccurrenceBranchDriverName", "Motorista não informado")} foi designado  '
                f'para a tarefa. Ao chegar ao local, confirmou a presença do veiculo da placa: {plate.upper()}, e chassi: {row.get("dataVehicleChassis", "Chassi não informado").upper()}, '
                f'abandonado e procedeu com a sua recolha. O veiculo foi encaminhado para o pátio da empresa para as devidas providências legais e contato.'
            )

        else:
            texts.append(
                f"Ocorrência registrada em {occurrence_dates[i]} às {occurrence_hours[i]} envolvendo o veículo "
                f"{model} de placa {plate}. Local da ocorrência: {data_address[i]}. "
                f"Última localização conhecida: {data_tracking_address[i]}. "
                f"Locatário: {user_name} (CPF: {user_cpf})."
            )
    
    # Gerar PDFs para cada registro
    for i, row in df.iterrows():
        plate = row['dataVehiclePlate']
        occurrence_type = int(row['dataOccurrenceType'])
        branch_id = row['dataBranchId']
        user_id = row['dataUserId']
        
        print(f"\n📝 Processando {i+1}/{len(df)}: Placa {plate} - Tipo {occurrence_type}")
        
        # Mapear tipos de ocorrência para nomes
        type_names = {
            1: "REGISTRO DE BOLETIM DE OCORRÊNCIA - ROUBO",
            2: "REGISTRO DE BOLETIM DE OCORRÊNCIA - INVENTÁRIO", 
            3: "REGISTRO DE BOLETIM DE OCORRÊNCIA - FURTO",
            4: "REGISTRO DE BOLETIM DE OCORRÊNCIA - VIOLAÇÃO",
            5: "REGISTRO DE BOLETIM DE OCORRÊNCIA - APROPRIAÇÃO INDÉBITA",
            6: "BAIXA DE BOLETIM DE OCORRÊNCIA - VEÍCULO ENCONTRADO",
            7: "BAIXA DE BOLETIM DE OCORRÊNCIA - VEÍCULO RECUPERADO",
            8: "BAIXA DE BOLETIM DE OCORRÊNCIA - VEÍCULO APREENDIDO",
            9: "BAIXA DE BOLETIM DE OCORRÊNCIA - VEÍCULO APREENDIDO - BO ATIVO",
            10: "ALTERAÇÂO DE BOLETIM DE OCORRÊNCIA - ROUBO/FURTO",
            11: "NÃO CRIMINAL - OUTROS NÃO CRIMINAL",
            12: "BAIXA DE BOLETIM DE OCORRÊNCIA - VEÍCULO ENCONTRADO SEM LOCAÇÃO"
        }
        
        doc_type_name = type_names.get(occurrence_type, "OCORRÊNCIA")
        
        # Preparar dados para substituição
        replacements = {
            'RAZAO_MOTTU': row.get('dataBranchIdName', 'MOTTU LOCACAO DE VEICULOS LTDA'),
            'ENDERECO_MOTTU': row.get('dataBranchAddress', 'Endereço não disponível'),
            'DATA_OCORRENCIA': occurrence_dates[i],
            'HORA_OCORRENCIA': occurrence_hours[i],
            'MARCA_MODELO': row.get('dataVehicleModel', 'Modelo não disponível'),
            'PLACA': plate,
            'NOME_LOCAT': data_user_full_name[i] if i < len(data_user_full_name) else 'Nome não disponível',
            'RG_LOCAT': data_user_rg[i] if i < len(data_user_rg) else 'RG não disponível',
            'CPF_LOCAT': data_user_cpf[i] if i < len(data_user_cpf) else 'CPF não disponível',
            'TELEFONE_LOCAT': user_phones[i] if i < len(user_phones) else 'Telefone não disponível',
            'LOCAL DO FATO: ENDERECO_OCORRENCIA': data_address[i] if i < len(data_address) else 'Endereço não disponível',
            'ENDERECO_LOCAT': data_user_address[i] if i < len(data_user_address) else 'Endereço não disponível',
            'DATA_INICIO_LOCACAO': '07/05/2025',  # Valor padrão, pode ser ajustado conforme necessidade
            'TEXTO': texts[i] if i < len(texts) else 'Histórico não disponível'
        }
        
        # Gerar PDF
        try:
            pdf_path = pdf_generator.generate_document_pdf(replacements, plate, doc_type_name, branch_id, user_id)
            if pdf_path:
                print(f"✅ PDF gerado com sucesso: {os.path.basename(pdf_path)}")
            else:
                print(f"❌ Falha ao gerar PDF para placa {plate}")
        except Exception as e:
            print(f"❌ Erro ao gerar PDF para placa {plate}: {e}")
        
        time.sleep(0.1)
    
    print(f"\n🎉 Processamento concluído! PDFs salvos em: {saidaPath}")

if __name__ == "__main__":
    main()