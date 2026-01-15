import os
import time
import requests
from pathlib import Path
import sys

# Garante que o pacote src seja encontrado quando rodar o script direto
# Precisa apontar para o diretório que contém a pasta "src", não para a pasta "src" em si
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.settings.auth import Auth
from src.settings.config import config
from src.utils.fileUtils import searchExcel
from src.settings.http import create_session, request_with_timeout

# Config values
# Endpoint de veículo: permite override por env VEHICLE_URL_TEMPLATE ou OPERATION_URL; fallback operation-backend
operation_base = os.getenv('OPERATION_URL') or 'https://operation-backend.mottu.cloud/api/v2'
vehicle_url_template = os.getenv('VEHICLE_URL_TEMPLATE') or f"{operation_base}/Veiculo/BuscarDetalheVeiculo/{{}}"
saidaPath = str(config.output_dir)
maxRetries = config.maxRetries
backoff = config.backoff

def limpar_pasta_crlv(crlv_path: str):
    try:
        if os.path.exists(crlv_path):
            for filename in os.listdir(crlv_path):
                file_path = os.path.join(crlv_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"Arquivo removido: {file_path}")
                except Exception as e:
                    print(f"Erro ao remover {file_path}: {e}")
            print(f"Pasta CRLV limpa com sucesso: {crlv_path}")
        else:
            print(f"Pasta CRLV não existe, criando: {crlv_path}")
            os.makedirs(crlv_path, exist_ok=True)
    except Exception as e:
        print(f"Erro ao limpar pasta CRLV: {e}")


def processVehicle(vehicleId, plate, userId, session=None, token=None, crlv_path=None):
    try:
        vehicleId = int(vehicleId)
        plate = str(plate).strip().upper()  # Normaliza a placa

        # Verificar se userId está vazio ou None
        if userId and str(userId).strip() != '':
            userId = str(userId).strip()
            print(f"Processando veículo - ID: {vehicleId}, Placa: {plate}, UserID: {userId}")
        else:
            userId = None
            print(f"Processando veículo - ID: {vehicleId}, Placa: {plate} (sem UserID)")

        url = vehicle_url_template.format(vehicleId)
        headers = {
            'accept': 'application/json',
            "Authorization": f"Bearer {token}"
        }

        if session:
            resp = request_with_timeout(session, 'GET', url, headers=headers, timeout=30)
        else:
            resp = requests.get(url, headers=headers, timeout=30)

        if not resp or getattr(resp, 'status_code', None) != 200:
            print(f'Erro na requisição do veículo {plate}: {getattr(resp, "status_code", "N/A")}')
            if resp is not None:
                print(f'Resposta: {getattr(resp, "text", "")[:200]}')
            return False

        data = resp.json()
        documentoUrl = data.get('dataResult', {}).get('documentoUrl')
        print(f"URL do Documento do Veículo {plate}: {documentoUrl}")

        if documentoUrl:
            # Definir nome do arquivo: plate_userId.pdf ou apenas plate.pdf se userId for vazio
            if userId:
                filename = f"{plate}_{userId}.pdf"
            else:
                filename = f"{plate}.pdf"

            local_filename = os.path.join(crlv_path, filename)
            os.makedirs(os.path.dirname(local_filename), exist_ok=True)

            if session:
                pdf_response = request_with_timeout(session, 'GET', documentoUrl, timeout=60)
            else:
                pdf_response = requests.get(documentoUrl, timeout=60)

            if getattr(pdf_response, 'status_code', None) == 200:
                with open(local_filename, 'wb') as file:
                    file.write(pdf_response.content)
                print(f'PDF do CRLV baixado e salvo como: {local_filename}')
                return True
            else:
                print(f'Falha ao baixar o PDF. Status code: {getattr(pdf_response, "status_code", "N/A")}')
                return False
        else:
            print(f'URL do documento não encontrada para o veículo {plate}')
            return False

    except Exception as e:
        print(f"[ERRO] Falha ao processar veículo {plate} (ID: {vehicleId}): {e}")
        return False


def main():
    try:
        vehicleIdList = searchExcel('dataVehicleId')
        plateList = searchExcel('dataVehiclePlate')
        rawUserList = searchExcel('dataUserId')  # Adicionado: buscar userIds
    except ValueError as e:
        print("Erro ao localizar o arquivo Excel:", e)
        print("Verifique a variável 'excel' no .env ou o caminho do arquivo Relatório BOs.xlsx.")
        return

    # Normaliza userId (remove .0 etc.)
    userIdList = []
    for raw in rawUserList:
        try:
            val = str(int(float(raw))).strip()
        except Exception:
            val = str(raw).strip()
        userIdList.append(val)

    token_obj = Auth()
    bearer_token = token_obj.get_token()
    if not bearer_token:
        print("Falha ao obter token. Abortando...")
        return

    # Criar queue com (vehicleId, plate, userId)
    queue = list(zip(vehicleIdList, plateList, userIdList))

    # Modificado: usar placa como chave para retentativas
    retries = {str(plate): 0 for plate in plateList}

    # Definir o caminho da pasta CRLV (permite override por env CRLV_PATH)
    crlv_path = str(Path(os.environ.get('CRLV_PATH', 'src/output/gerador/crlv')).resolve())

    # Limpa pasta
    limpar_pasta_crlv(crlv_path)

    session = create_session(retries=2, backoff_factor=0.2)

    while queue:
        vehicleId, plate, userId = queue.pop(0)
        print(f"Iniciando processamento do veículo: {plate} (ID: {vehicleId})")

        ok = processVehicle(vehicleId, plate, userId, session=session, token=bearer_token, crlv_path=crlv_path)

        if ok:
            print(f"Processamento concluído para o veículo: {plate}")
            continue
        else:
            retries[str(plate)] += 1
            if retries[str(plate)] < maxRetries:
                print(f"Reprocessando veículo: {plate} (Tentativa {retries[str(plate)]})")
                time.sleep(backoff)
                queue.append((vehicleId, plate, userId))
            else:
                print(f"Número máximo de tentativas excedido para o veículo: {plate}")


if __name__ == "__main__":
    main()