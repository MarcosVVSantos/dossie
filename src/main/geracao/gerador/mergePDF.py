import os
import shutil
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from PyPDF2 import PdfMerger, PdfReader
import re
import glob
import sys

# Garante que o pacote src seja encontrado quando rodar o script direto
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.settings.config import config

# Configuração de caminhos via Config
# BASE_PATH deve apontar para 'src/output/gerador'
BASE_PATH = project_root / "src" / "output" / "gerador"
print(f"Usando BASE_PATH: {BASE_PATH}")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Definir DONE_PATH globalmente
DONE_PATH = BASE_PATH / "done"

def limpar_pasta_done():
    """Remove e recria a pasta DONE_PATH."""
    try:
        if DONE_PATH.exists():
            shutil.rmtree(DONE_PATH)
            print(f"Pasta 'done' removida: {DONE_PATH}")
        DONE_PATH.mkdir(parents=True, exist_ok=True)
        print(f"Pasta 'done' criada: {DONE_PATH}")
    except Exception as e:
        print(f"Erro ao limpar/criar pasta done: {e}")

def carregar_dados_excel():
    """
    Lê o Excel definido em .env e retorna um dict:
    { "<placa>_<userId>": tipo_documento (int) }

    Tenta colunas alternativas (dataUserRentalId, dataVehicleId) e extração por regex
    antes de pular a linha. Emita debug por linha.
    """
    try:
        excel_env = os.getenv('excel') or str(config.excel)
        project_root = Path(__file__).resolve().parents[4]

        if excel_env:
            excel_path = Path(os.path.expanduser(excel_env))
            if not excel_path.is_absolute():
                excel_path = (project_root / excel_path).resolve()
        else:
            excel_path = (project_root / "src" / "utils" / "Relatório BOs.xlsx").resolve()

        print(f"[DEBUG] excel_path resolvido: {excel_path}")
        if not excel_path.exists():
            print(f"Erro: arquivo Excel não encontrado: {excel_path}")
            try:
                nearby = list((project_root / "src" / "utils").glob("*.xlsx"))
                print(f"[DEBUG] Arquivos .xlsx em src/utils: {[p.name for p in nearby]}")
            except Exception:
                pass
            return {}

        xl = pd.ExcelFile(str(excel_path))
        sheet_env = os.getenv('excelPage')
        sheet_name = sheet_env if sheet_env else xl.sheet_names[0]
        print(f"[DEBUG] Usando sheet: {sheet_name}")

        df = pd.read_excel(str(excel_path), sheet_name=sheet_name)
        print(f"[DEBUG] Excel carregado: shape={df.shape}")
        print(f"[DEBUG] Colunas encontradas: {df.columns.tolist()}")

        required = ['dataVehiclePlate']
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"Erro: colunas essenciais ausentes no Excel: {missing}")
            return {}

        mapping = {}
        for idx, row in df.iterrows():
            placa = str(row.get('dataVehiclePlate', '')).strip()
            user = row.get('dataUserId', None)
            tipo = row.get('dataOccurrenceType', None)

            def normalize_candidate(val):
                if pd.isna(val):
                    return None
                s = str(val).strip()
                if s in ('', '-', 'NaN', 'None'):
                    return None
                try:
                    return str(int(float(s)))
                except Exception:
                    return s

            user_str = normalize_candidate(user)
            source = 'dataUserId'

            # tenta alternativas se user inválido
            if not user_str:
                for alt_col in ('dataUserRentalId', 'dataVehicleId'):
                    if alt_col in df.columns:
                        alt_val = normalize_candidate(row.get(alt_col))
                        if alt_val:
                            user_str = alt_val
                            source = alt_col
                            break

            # tenta extrair dígitos de qualquer célula da linha
            if not user_str:
                combined = ' '.join([str(v) for v in row.values if pd.notna(v)])
                m = re.search(r'\d{3,}', combined)
                if m:
                    user_str = m.group(0)
                    source = 'regex'

            if not user_str:
                print(f"[DEBUG] Linha {idx} ignorada: userId ausente. placa='{placa}'")
                continue

            if not placa:
                print(f"[DEBUG] Linha {idx} ignorada: placa ausente. user='{user_str}' (fonte: {source})")
                continue

            chave = f"{placa}_{user_str}"
            try:
                mapping[chave] = int(tipo) if (tipo is not None and not pd.isna(tipo)) else None
            except Exception:
                mapping[chave] = None

            print(f"[DEBUG] Linha {idx} -> chave='{chave}' (fonte: {source})")

        print(f"Carregado mapeamento Excel: {len(mapping)} entradas")
        return mapping
    except Exception as e:
        print(f"Erro ao carregar Excel para mapeamento: {e}")
        return {}

# Função utilitária para validar PDF
def is_valid_pdf(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return False
        # tenta abrir com PdfReader (validação rápida)
        PdfReader(str(path))
        return True
    except Exception:
        return False

def extrair_chave_sem_data(nome_arquivo):
    """
    Extrai a chave (PLACA_USERID) do nome do arquivo, removendo datas e outros sufixos.
    Exemplos:
    - "ABC1234_56789_20241225_120000.pdf" -> "ABC1234_56789"
    - "ABC1234_56789.pdf" -> "ABC1234_56789" 
    - "ABC1234_56789_BO_1.pdf" -> "ABC1234_56789"
    """
    # Remove extensão
    nome_sem_ext = Path(nome_arquivo).stem
    
    # Padrão para identificar e remover datas (YYYYMMDD_HHMMSS)
    padrao_data = r'_\d{8}_\d{6}$'
    nome_sem_data = re.sub(padrao_data, '', nome_sem_ext)
    
    # Para BOs, remove também o sufixo "_BO_TIPO"
    if '_BO_' in nome_sem_data:
        partes = nome_sem_data.split('_')
        # Mantém apenas placa e user ID (primeiras duas partes)
        if len(partes) >= 2:
            nome_sem_data = f"{partes[0]}_{partes[1]}"
    
    return nome_sem_data

def merge_pdfs():
    """Junta os PDFs das pastas na ordem especificada"""
    
    # Limpar pasta done antes de iniciar
    print("🧹 Limpando pasta done...")
    limpar_pasta_done()
    
    # Carregar mapeamento do Excel
    print("📊 Carregando dados do Excel...")
    mapeamento_placa_tipo = carregar_dados_excel()
    if not mapeamento_placa_tipo:
        print("❌ Não foi possível carregar o mapeamento do Excel")
        return
    
    # Configurações de caminhos (usa BASE_PATH já definido no topo)
    DONE_PATH = BASE_PATH / "done"
    
    # Configuração das pastas de origem
    pastas_config = {
        "DOCUMENTO_GERADO": BASE_PATH / "document",
        "CNH": BASE_PATH / "cnh", 
        "CRLV": BASE_PATH / "crlv",
        "CONTRATO": BASE_PATH / "contract",
        "BO": BASE_PATH / "bo"
    }
    
    # Verificar se as pastas existem
    for nome, pasta in pastas_config.items():
        if not pasta.exists():
            print(f"❌ Pasta não encontrada: {pasta} ({nome})")
            return
    
    print("📁 Pastas verificadas com sucesso!")
    
    # Buscar PDFs válidos em cada pasta
    pdfs_por_pasta = {}
    for nome, pasta in pastas_config.items():
        pdf_files = [f for f in pasta.glob("*.pdf") if is_valid_pdf(f)]
        pdfs_por_pasta[nome] = pdf_files
        print(f"📄 {nome}: {len(pdf_files)} arquivos encontrados")
    
    # Agrupar documentos por chave (placa_userId) - USANDO EXTRAÇÃO SEM DATA
    documentos_por_chave = {}
    
    # Processar documentos das pastas principais (SEM CNH - CNH será processada separadamente)
    pastas_principais = ["DOCUMENTO_GERADO", "CRLV", "CONTRATO"]
    for pasta_nome in pastas_principais:
        for pdf_path in pdfs_por_pasta[pasta_nome]:
            # Extrai chave sem data do nome do arquivo
            chave = extrair_chave_sem_data(pdf_path.name)
            if "_" in chave:  # Verifica formato PLACA_USERID
                documentos_por_chave.setdefault(chave, {})[pasta_nome] = pdf_path
                print(f"🔹 {pasta_nome} - Chave: {chave} - Arquivo: {pdf_path.name}")
    
    # Processar CNH: processar todos os arquivos com padrão placa_userId.pdf
    for pdf_path in pdfs_por_pasta["CNH"]:
        # Extrai chave sem data do nome do arquivo
        chave = extrair_chave_sem_data(pdf_path.name)
        if "_" in chave:  # Verifica formato PLACA_USERID
            documentos_por_chave.setdefault(chave, {})["CNH"] = pdf_path
            print(f"🔹 CNH - Chave: {chave} - Arquivo: {pdf_path.name}")
    
    # Processar BOs (formato especial pode incluir datas e sufixos)
    for pdf_path in pdfs_por_pasta["BO"]:
        # Extrai chave sem data e sem sufixo BO
        chave = extrair_chave_sem_data(pdf_path.name)
        
        if "_" in chave:  # Verifica se tem formato válido
            documentos_por_chave.setdefault(chave, {})["BO"] = pdf_path
            print(f"🔹 BO - Chave: {chave} - Arquivo: {pdf_path.name}")
    
    print(f"\n🎯 Total de chaves encontradas: {len(documentos_por_chave)}")
    
    # DEBUG: Mostrar todas as chaves encontradas
    print("\n🔍 DEBUG - Chaves encontradas:")
    for chave in sorted(documentos_por_chave.keys()):
        print(f"   {chave}: {list(documentos_por_chave[chave].keys())}")
    
    # Definir regras de documentos por tipo
    def get_documentos_obrigatorios(tipo):
        """Retorna lista de documentos obrigatórios baseado no tipo"""
        if tipo in [4, 10]:
            return ["DOCUMENTO_GERADO", "CNH", "CRLV"]
        elif tipo in [11, 12]:
            return ["DOCUMENTO_GERADO", "CRLV"]
        else:
            return ["DOCUMENTO_GERADO", "CNH", "CRLV", "CONTRATO"]
    
    def get_ordem_documentos(documentos, tipo):
        """Define ordem dos documentos baseado no tipo"""
        ordem_base = []
        
        # Documentos base
        if tipo in [4, 10]:
            ordem_base = [
                documentos["DOCUMENTO_GERADO"],
                documentos["CNH"], 
                documentos["CRLV"]
            ]
        elif tipo in [11, 12]:
            ordem_base = [
                documentos["DOCUMENTO_GERADO"],
                documentos["CRLV"]
            ]
        else:
            ordem_base = [
                documentos["DOCUMENTO_GERADO"],
                documentos["CNH"],
                documentos["CRLV"], 
                documentos["CONTRATO"]
            ]
        
        # Adicionar BO se necessário
        if tipo in [6, 7, 8, 9, 10] and "BO" in documentos:
            ordem_base.append(documentos["BO"])
            print(f"🔸 Tipo {tipo} detectado - BO será incluído")
        
        return ordem_base
    
    # Encontrar conjuntos completos
    conjuntos_completos = []
    conjuntos_incompletos = {}
    
    for chave, documentos in documentos_por_chave.items():
        tipo_documento = mapeamento_placa_tipo.get(chave)
        if tipo_documento is None:
            print(f"⚠️  Tipo de documento não encontrado para: {chave}")
            continue
        
        documentos_obrigatorios = get_documentos_obrigatorios(tipo_documento)
        tem_todos = all(doc in documentos for doc in documentos_obrigatorios)
        
        if tem_todos:
            ordem = get_ordem_documentos(documentos, tipo_documento)
            
            conjuntos_completos.append({
                'chave': chave,
                'tipo_documento': tipo_documento,
                'documentos': documentos,
                'ordem': ordem
            })
            print(f"✅ Conjunto completo encontrado para: {chave} - Tipo: {tipo_documento}")
        else:
            documentos_faltantes = [doc for doc in documentos_obrigatorios if doc not in documentos]
            print(f"⚠️  Conjunto incompleto para {chave}. Faltando: {documentos_faltantes}")
            conjuntos_incompletos[chave] = documentos
    
    print(f"\n📊 Conjuntos completos: {len(conjuntos_completos)}")
    
    if not conjuntos_completos:
        print("❌ Nenhum conjunto completo encontrado!")
        print("\n🔍 DEBUG - Documentos por chave:")
        for chave, docs in documentos_por_chave.items():
            print(f"   {chave}: {list(docs.keys())}")
        return
    
    # Mapeamento de tipos de documento
    tipo_documento_map = {
        1: "REGISTRO_DE_BOLETIM_DE_OCORRENCIA_ROUBO",
        2: "REGISTRO_DE_BOLETIM_DE_OCORRENCIA_INVENTARIO", 
        3: "REGISTRO_DE_BOLETIM_DE_OCORRENCIA_FURTO",
        4: "REGISTRO_DE_BOLETIM_DE_OCORRENCIA_VIOLACAO",
        5: "REGISTRO_DE_BOLETIM_DE_OCORRENCIA_APROPRIACAO_INDEBITA",
        6: "REGISTRO_DE_BOLETIM_DE_OCORRENCIA_VEICULO_ENCONTRADO",
        7: "BAIXA_DE_BOLETIM_DE_OCORRENCIA_VEICULO_RECUPERADO",
        8: "BAIXA_DE_BOLETIM_DE_OCORRENCIA_VEICULO_APREENDIDO",
        9: "BAIXA_DE_BOLETIM_DE_OCORRENCIA_VEICULO_APREENDIDO_BO_ATIVO",
        10: "ALTERACAO_DE_BOLETIM_DE_OCORRENCIA_ROUBO_FURTO",
        11: "NAO CRIMINAL - OUTROS NAO CRIMINAL",
        12: "BAIXA_DE_BOLETIM_DE_OCORRENCIA_VEICULO_ENCONTRADO_SEM_LOCACAO"
    }
    
    # Agrupar e processar conjuntos por tipo
    conjuntos_por_tipo = {}
    for conjunto in conjuntos_completos:
        tipo = conjunto['tipo_documento']
        conjuntos_por_tipo.setdefault(tipo, []).append(conjunto)
    
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Processar conjuntos completos
    for tipo_documento, conjuntos in conjuntos_por_tipo.items():
        print(f"\n📂 Processando tipo de documento: {tipo_documento}")
        
        pasta_tipo = DONE_PATH / f"{tipo_documento}_{data_hora}"
        pasta_tipo.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Criada pasta: {pasta_tipo.name}")
        print(f"📄 Processando {len(conjuntos)} conjuntos para este tipo")
        
        for conjunto in conjuntos:
            chave = conjunto['chave']
            arquivos_ordem = conjunto['ordem']
            
            print(f"  🔄 Processando: {chave}")
            
            try:
                with PdfMerger() as merger:
                    for arquivo in arquivos_ordem:
                        merger.append(str(arquivo))
                    
                    placa = chave.split("_")[0]
                    arquivo_mesclado = f"{tipo_documento}_{placa}_{data_hora}.pdf"
                    caminho_mesclado = pasta_tipo / arquivo_mesclado
                    
                    # Escrever atomicamente
                    tmp_path = caminho_mesclado.with_suffix(".tmp")
                    merger.write(str(tmp_path))
                    tmp_path.replace(caminho_mesclado)
                    
                print(f"    ✅ PDF mesclado salvo: {arquivo_mesclado}")
                
            except Exception as e:
                print(f"    ❌ Erro ao processar {chave}: {e}")
    
    # Processar conjuntos incompletos
    if conjuntos_incompletos:
        pasta_incompletos = DONE_PATH / f"INCOMPLETOS_{data_hora}"
        pasta_incompletos.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📦 Processando conjuntos incompletos...")
        
        for chave, documentos in conjuntos_incompletos.items():
            try:
                subpasta_chave = pasta_incompletos / chave
                subpasta_chave.mkdir(parents=True, exist_ok=True)
                
                for doc_type, pdf_path in documentos.items():
                    nome_arquivo = f"{doc_type}_{pdf_path.name}"
                    destino = subpasta_chave / nome_arquivo
                    shutil.copy2(pdf_path, destino)
                
                print(f"   📄 Copiados documentos incompletos para: {chave}")
                
            except Exception as e:
                print(f"   ❌ Erro ao copiar documentos incompletos {chave}: {e}")
    
    # Resumo final
    print(f"\n🎉 PROCESSAMENTO CONCLUÍDO!")
    print(f"📊 RESUMO:")
    print(f"   ✅ Dossiês completos mesclados: {len(conjuntos_completos)}")
    print(f"   📁 Pastas criadas: {len(conjuntos_por_tipo)} tipos diferentes")
    for tipo, quantidade in conjuntos_por_tipo.items():
        nome_tipo = tipo_documento_map.get(tipo, f"Tipo_{tipo}")
        print(f"      - Tipo {tipo} ({nome_tipo}): {len(quantidade)} dossiês")
    print(f"   ⚠️  Conjuntos incompletos: {len(conjuntos_incompletos)}")
    print(f"📁 Pasta de resultados: {DONE_PATH}")
    print(f"📑 ORDEM DOS PDFs MESCLADOS:")
    print(f"   1. 📄 Documento Gerado (document)")
    print(f"   2. 🪪 CNH (cnh)") 
    print(f"   3. 🚗 CRLV (crlv)")
    print(f"   4. 📝 Contrato (contract) - EXCETO para Tipos 4, 10, 11 e 12")
    print(f"   5. 📋 BO (bo) - APENAS para Tipos 6, 7, 8, 9 e 10")
    print(f"   ⚠️  NOTA: Para Tipos 4 (VIOLAÇÃO) e 10 (ALTERAÇÃO ROUBO/FURTO), o CONTRATO não é incluído")
    print(f"   📋 NOTA: Para Tipo 11 e 12, CONTRATO não é incluído - apenas DOCUMENTO e CRLV")
    print(f"   📋 NOTA: Para Tipos 6, 7, 8, 9 e 10, o BO é incluído como último documento")

if __name__ == "__main__":
    print("🔄 Iniciando mesclagem de PDFs para dossiês completos...")
    merge_pdfs()