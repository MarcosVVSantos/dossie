#!/usr/bin/env python3
"""
Debug script to check Excel data and file matching
"""
import os
from src.utils.fileUtils import searchExcel
from src.settings.config import config

def debug_excel_data():
    """Check what data is in the Excel file"""
    print("=== DADOS DO EXCEL ===")
    
    try:
        userList = searchExcel('dataUserId')
        branchList = searchExcel('dataBranchId')
        plateList = searchExcel('dataVehiclePlate')
        rentalList = searchExcel('dataUserRentalId')
        
        print(f"Número de registros: {len(plateList)}")
        print(f"Placas: {plateList}")
        print(f"User IDs: {userList}")
        print(f"Branch IDs: {branchList}")
        print(f"Rental IDs: {rentalList}")
        
        return plateList, userList, rentalList, branchList
        
    except Exception as e:
        print(f"Erro ao ler Excel: {e}")
        return [], [], [], []

def check_file_existence(plateList, userList, rentalList, branchList):
    """Check which files actually exist"""
    print("\n=== VERIFICAÇÃO DE ARQUIVOS ===")
    
    saida_path = os.getenv('saida')
    if not saida_path:
        print("❌ Caminho de saída não definido")
        return
    
    # List existing files in each directory
    directories = {
        'contract': f'{saida_path}/contract',
        'cnh': f'{saida_path}/cnh',
        'crlv': f'{saida_path}/crlv',
        'document': f'{saida_path}/document'
    }
    
    existing_files = {}
    for dir_name, dir_path in directories.items():
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith('.pdf')]
            existing_files[dir_name] = files
            print(f"{dir_name.upper()}: {files}")
        else:
            print(f"❌ Diretório não existe: {dir_path}")
    
    print("\n=== ANÁLISE DE CORRESPONDÊNCIA ===")
    
    for i, (plate, user_id, rental_id, branch_id) in enumerate(zip(plateList, userList, rentalList, branchList)):
        print(f"\nRegistro {i+1}: {plate}")
        print(f"  User ID: {user_id}")
        print(f"  Rental ID: {rental_id}")
        print(f"  Branch ID: {branch_id}")
        
        # Check expected files
        expected_files = {
            'document': f'{plate}.html',
            'crlv': f'{plate}.pdf',
            'cnh': f'{user_id}.pdf',
            'contract': f'{rental_id}.pdf'
        }
        
        for file_type, expected_file in expected_files.items():
            if file_type in existing_files:
                if file_type == 'document':
                    # Check HTML file
                    html_path = f'{saida_path}/document/{expected_file}'
                    exists = os.path.exists(html_path)
                    print(f"  {file_type.upper()}: {expected_file} {'✅' if exists else '❌'}")
                else:
                    # Check PDF file
                    exists = expected_file in existing_files[file_type]
                    print(f"  {file_type.upper()}: {expected_file} {'✅' if exists else '❌'}")
                    if not exists and file_type in existing_files:
                        print(f"    Arquivos disponíveis: {existing_files[file_type]}")

def main():
    """Run all diagnostics"""
    print("DIAGNÓSTICO DE DADOS E ARQUIVOS")
    print("=" * 50)
    
    plateList, userList, rentalList, branchList = debug_excel_data()
    
    if plateList:
        check_file_existence(plateList, userList, rentalList, branchList)
    
    print("\n" + "=" * 50)
    print("DIAGNÓSTICO CONCLUÍDO")

if __name__ == "__main__":
    main()
