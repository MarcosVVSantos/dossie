import os
import pandas as pd

def _project_root_from_utils():
    # src/utils -> subir dois níveis para chegar na raiz do projeto
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def resolve_excel_path(env_excel_value):
    if not env_excel_value:
        return None
    path = os.path.expanduser(env_excel_value)
    if not os.path.isabs(path):
        path = os.path.abspath(os.path.join(_project_root_from_utils(), path))
    return path

def searchExcel(column_name, excelPath=None):
    """
    Lê a planilha definida em .env (variável 'excel') e retorna a lista da coluna.
    Se excelPath for fornecido, usa-o (aceita relativo ao projeto).
    """
    # evita import circular de dotenv aqui - espera-se que .env já esteja carregado
    if not excelPath:
        excelPath = os.getenv('excel')

    excelPath = resolve_excel_path(excelPath)
    if not excelPath or not os.path.exists(excelPath):
        raise ValueError(f"Caminho do arquivo Excel inválido ou não encontrado: {excelPath}")

    df = pd.read_excel(excelPath, sheet_name=os.getenv('excelPage', 0))
    if column_name not in df.columns:
        return []
    # limpa valores NaN e converte para string
    return [x for x in df[column_name].fillna('').tolist()]