import json
import requests

from src.settings.auth import Auth
from src.settings.config import config
from src.settings.http import create_session, request_with_timeout


def test_authentication():
    """Testa se a autenticação está funcionando corretamente"""
    print("=== TESTE DE AUTENTICAÇÃO ===")
    try:
        auth = Auth()
        token = auth.get_token()
        if token:
            print(f"✅ Autenticação bem-sucedida")
            print(f"Token (primeiros 20 chars): {token[:20]}...")
            return token
        else:
            print("❌ Falha na autenticação - token vazio")
            return None
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return None

def test_api_endpoints(token):
    """Testa se os endpoints da API estão respondendo"""
    print("\n=== TESTE DE ENDPOINTS ===")

    endpoints = {
        'imageProcessUrl': config.imageProcessUrl,
        'fileToolsUrl': config.fileToolsUrl,
        'backendUrl': config.backendUrl
    }

    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    session = create_session(retries=2, backoff_factor=0.2)

    for name, url in endpoints.items():
        if not url:
            print(f"❌ {name}: URL não definida nas config")
            continue

        try:
            # Teste simples de conectividade
            resp = request_with_timeout(session, 'GET', url, headers=headers, timeout=10)
            print(f"✅ {name}: Status {getattr(resp, 'status_code', 'N/A')}")
            if getattr(resp, 'status_code', None) != 200:
                text = getattr(resp, 'text', '')[:100]
                print(f"   Conteúdo: {text}...")
        except requests.exceptions.Timeout:
            print(f"❌ {name}: Timeout (>10s)")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Erro de conexão")
        except Exception as e:
            print(f"❌ {name}: {e}")

def test_html_to_pdf_api(token):
    """Testa especificamente o endpoint de HTML para PDF"""
    print("\n=== TESTE HTML PARA PDF ===")

    fileToolsUrl = config.fileToolsUrl
    if not fileToolsUrl:
        print("❌ fileToolsUrl não definida nas config")
        return

    url = f"{fileToolsUrl}/pdf/html-to-pdf"

    # HTML simples para teste
    test_payload = {
        "html": "<html><body><h1>Teste</h1></body></html>",
        "css": ""
    }

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    session = create_session(retries=2, backoff_factor=0.2)

    try:
        response = request_with_timeout(session, 'POST', url, headers=headers, data=json.dumps(test_payload), timeout=30)
        print(f"Status da resposta: {getattr(response, 'status_code', 'N/A')}")
        print(f"Headers da resposta: {dict(getattr(response, 'headers', {}))}")
        print(f"Tamanho do conteúdo: {len(getattr(response, 'content', b''))} bytes")

        if getattr(response, 'content', None):
            try:
                result = response.json()
                print(f"✅ JSON válido recebido")
                if 'dataResult' in result:
                    print(f"✅ Campo 'dataResult' presente")
                else:
                    print(f"❌ Campo 'dataResult' ausente. Campos disponíveis: {list(result.keys())}")
            except json.JSONDecodeError as e:
                print(f"❌ Resposta não é JSON válido: {e}")
                print(f"Primeiros 200 chars: {getattr(response, 'text', '')[:200]}")
        else:
            print("❌ Resposta vazia")

    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def check_docx_files():
    """Verifica se os arquivos DOCX existem e são válidos"""
    print("\n=== VERIFICAÇÃO DE ARQUIVOS DOCX ===")

    saida_path = str(config.output_dir)
    if not saida_path:
        print("❌ Caminho de saída não definido nas config")
        return

    documents_path = os.path.join(saida_path, "document")

    if not os.path.exists(documents_path):
        print(f"❌ Diretório não existe: {documents_path}")
        return

    docx_files = [f for f in os.listdir(documents_path) if f.endswith('.docx')]

    if not docx_files:
        print("❌ Nenhum arquivo DOCX encontrado")
        return

    print(f"Encontrados {len(docx_files)} arquivos DOCX:")

    for filename in docx_files:
        filepath = os.path.join(documents_path, filename)
        try:
            size = os.path.getsize(filepath)
            print(f"✅ {filename}: {size} bytes")
        except Exception as e:
            print(f"❌ {filename}: Erro ao ler arquivo - {e}")

def main():
    """Executa todos os testes de diagnóstico"""
    print("DIAGNÓSTICO DO SISTEMA DE CONVERSÃO DE DOCUMENTOS")
    print("=" * 50)
    
    # Teste de autenticação
    token = test_authentication()
    
    if token:
        # Teste de endpoints
        test_api_endpoints(token)
        
        # Teste específico do HTML para PDF
        test_html_to_pdf_api(token)
    
    # Verificação de arquivos
    check_docx_files()
    
    print("\n" + "=" * 50)
    print("DIAGNÓSTICO CONCLUÍDO")

if __name__ == "__main__":
    main()
