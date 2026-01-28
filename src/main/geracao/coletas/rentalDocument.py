import sys
from pathlib import Path

# IMPORTANTE: Configurar sys.path ANTES de qualquer outro import
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import os
import time
import requests

from src.settings.auth import Auth
from src.settings.config import config
from src.utils.fileUtils import searchExcel
from src.settings.http import create_session, request_with_timeout


# Variáveis carregadas via config
paymentsUrl = config.paymentsUrl
saidaPath = str(config.output_dir)
maxRetries = config.maxRetries
backoff = config.backoff


# Definir o caminho da pasta contract (pode ser sobrescrito via variável de ambiente CONTRACT_PATH)
contract_path = str(config.contract_path)


def limpar_pasta_contract():
    """
    Limpa a pasta contract antes de iniciar o processamento
    """
    try:
        if os.path.exists(contract_path):
        
            for filename in os.listdir(contract_path):
                file_path = os.path.join(contract_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"Arquivo removido: {file_path}")
                except Exception as e:
                    print(f"Erro ao remover {file_path}: {e}")
            print(f"Pasta contract limpa com sucesso: {contract_path}")
        else:
            print(f"Pasta contract não existe, criando: {contract_path}")
            os.makedirs(contract_path, exist_ok=True)
    except Exception as e:
        print(f"Erro ao limpar pasta contract: {e}")

def processRental(userId, rentalId, plate, retry_count=0, session=None, token=None):
    try:
        userId = int(userId)
        rentalId = int(rentalId)
        plate = str(plate).strip().upper()

        url = f"{paymentsUrl}/ContratoModelo/GerarDocumentoAdmin/{userId}"
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {token}'}

        # Use session if fornecido, senão requests diretamente
        if session:
            response = request_with_timeout(session, 'GET', url, headers=headers, timeout=60)
        else:
            response = requests.get(url, headers=headers, timeout=60, verify=True)

        if response is None:
            print(f'❌ Erro ao requisitar URL do contrato para usuário {userId}')
            return False

        try:
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"❌ Erro ao processar resposta JSON do contrato: {e}")
            return False

        documentoUrl = data.get('dataResult', {}).get('documentoUrl')

        localFilename = os.path.join(contract_path, f"{plate}_{userId}.pdf")
        os.makedirs(os.path.dirname(localFilename), exist_ok=True)

        if documentoUrl:
            if session:
                pdf_response = request_with_timeout(session, 'GET', documentoUrl, timeout=60)
            else:
                pdf_response = requests.get(documentoUrl, timeout=60)

            if pdf_response and getattr(pdf_response, 'status_code', None) == 200:
                with open(localFilename, 'wb') as file:
                    file.write(pdf_response.content)
                print(f'✅ PDF baixado: {localFilename}')
                return True
            else:
                code = getattr(pdf_response, 'status_code', 'N/A')
                print(f'❌ Falha ao baixar PDF. Status: {code}')
                return False
        else:
            print(f'❌ URL do documento não encontrada para usuário {userId}')
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout ao processar contrato - Usuário: {userId}, Rental: {rentalId}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Erro de conexão - Usuário: {userId}, Rental: {rentalId}: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⚠️ Processamento interrompido pelo usuário")
        raise
    except Exception as e:
        print(f"❌ Erro ao processar contrato - Usuário: {userId}, Rental: {rentalId}: {e}")
        return False


def main():
    # prepara listas de trabalho lendo o Excel
    rentalIdList = searchExcel('dataUserRentalId')
    userIdList = searchExcel('dataUserId')
    plateList = searchExcel('dataVehiclePlate')  # Adicionado: buscar placas
    occurrenceTypeList = searchExcel('dataOccurrenceType')  # Buscar tipo de ocorrência

    # Criar queue com (userId, rentalId, plate) e filtrar tipo 12 (não precisa de contrato)
    queue = []
    for uid, rid, plate, occ_type in zip(userIdList, rentalIdList, plateList, occurrenceTypeList):
        try:
            occ_type_int = int(occ_type) if occ_type not in (None, '-', '') else 0
        except (ValueError, TypeError):
            occ_type_int = 0
        
        # Pular tipo 12 (VEICULO ENCONTRADO SEM LOCACAO) - não precisa de contrato
        if occ_type_int == 12:
            print(f"⏭️  Pulando contrato para tipo 12 (VEÍCULO ENCONTRADO SEM LOCAÇÃO) - Placa: {plate}")
            continue
        
        queue.append((uid, rid, plate))
    
    retries = {f"{uid}_{rid}": 0 for uid, rid, _, _ in zip(userIdList, rentalIdList, plateList, occurrenceTypeList)}

    # Limpa pasta
    limpar_pasta_contract()

    token_obj = Auth()
    bearer_token = token_obj.get_token()
    if not bearer_token:
        print("Falha ao obter token. Abortando...")
        return

    session = create_session(retries=2, backoff_factor=0.2)

    while queue:
        userId, rentalId, plate = queue.pop(0)
        print(f"Processando contrato - Usuário: {userId}, Rental: {rentalId}, Placa: {plate}")
        ok = processRental(userId, rentalId, plate, session=session, token=bearer_token)
        if ok:
            print(f"Processamento concluído para o contrato - Usuário: {userId}, Rental: {rentalId}")
            continue
        else:
            key = f"{userId}_{rentalId}"
            retries[key] += 1
            if retries[key] < maxRetries:
                print(f"Reprocessando contrato - Usuário: {userId}, Rental: {rentalId} (Tentativa {retries[key]})")
                time.sleep(backoff)
                queue.append((userId, rentalId, plate))
            else:
                print(f"Número máximo de tentativas excedido para contrato - Usuário: {userId}, Rental: {rentalId}")


if __name__ == "__main__":
    main()
