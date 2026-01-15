#!/usr/bin/env python3
"""
Test script to verify the document conversion fixes
"""
import os
from src.utils.documentUtils import convertDocxToPdf, convertPdf
from src.settings.config import config

def test_html_to_pdf():
    """Testa a conversão de HTML para PDF"""
    print("=== TESTE: HTML PARA PDF ===")
    
    test_html = """
    <html>
    <head>
        <title>Teste de Conversão</title>
    </head>
    <body>
        <h1>Documento de Teste</h1>
        <p>Este é um teste da conversão de HTML para PDF.</p>
        <p>Se você está vendo esta mensagem, a conversão funcionou!</p>
    </body>
    </html>
    """
    
    try:
        result = convertHtmlToPdf(test_html)
        if result:
            print(f"✅ Conversão bem-sucedida! Base64 gerado ({len(result)} caracteres)")
            return True
        else:
            print("❌ Conversão falhou - resultado vazio")
            return False
    except Exception as e:
        print(f"❌ Erro na conversão: {e}")
        return False

def test_docx_to_base64():
    """Testa a conversão de DOCX para Base64"""
    print("\n=== TESTE: DOCX PARA BASE64 ===")
    
    # Procura por arquivos DOCX na pasta de saída
    from dotenv import load_dotenv
    load_dotenv()
    
    saida_path = os.getenv('saida')
    if not saida_path:
        print("❌ Caminho de saída não definido")
        return False
    
    documents_path = os.path.join(saida_path, "document")
    
    if not os.path.exists(documents_path):
        print(f"❌ Diretório não existe: {documents_path}")
        return False
    
    docx_files = [f for f in os.listdir(documents_path) if f.endswith('.docx')]
    
    if not docx_files:
        print("❌ Nenhum arquivo DOCX encontrado para teste")
        return False
    
    # Testa o primeiro arquivo
    test_file = os.path.join(documents_path, docx_files[0])
    
    try:
        result = convertDocxToBs64(test_file)
        if result:
            print(f"✅ Conversão bem-sucedida! Base64 gerado para {docx_files[0]} ({len(result)} caracteres)")
            return True
        else:
            print(f"❌ Conversão falhou para {docx_files[0]}")
            return False
    except Exception as e:
        print(f"❌ Erro na conversão de {docx_files[0]}: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("TESTE DAS CORREÇÕES DE CONVERSÃO DE DOCUMENTOS")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # Teste HTML para PDF
    if test_html_to_pdf():
        success_count += 1
    
    # Teste DOCX para Base64
    if test_docx_to_base64():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"RESULTADO: {success_count}/{total_tests} testes passaram")
    
    if success_count == total_tests:
        print("🎉 Todos os testes passaram! As correções funcionaram.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")

if __name__ == "__main__":
    main()
