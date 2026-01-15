import json
import os
import io
import sys
import time
import PyPDF2
import base64 as bs64
from dotenv import load_dotenv
import requests
import subprocess
import tempfile
from docx2pdf import convert

from src.settings.auth import Auth
from src.settings.config import config

imageProcessUrl = config.imageProcessUrl
fileToolsUrl = config.fileToolsUrl
maxRetries = config.maxRetries
docxPath = os.environ.get('docx')  # optional and not in config
token = Auth()

def convertDocxToPdf(docx_file):
    if not os.path.exists(docx_file):
        print(f"O arquivo DOCX {docx_file} não foi encontrado.")
        return None

    try:
        with open(docx_file, 'rb') as file:
            doc_bytes = file.read()
        return bs64.b64encode(doc_bytes).decode('utf-8')
    except Exception as e:
        print(f"Erro ao converter DOCX para PDF: {e}")
        return None

def convertPdf(string_bs64, path):
    try:
        pdf_bytes = bs64.b64decode(string_bs64)
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        pdf_writer = PyPDF2.PdfWriter()
        
        for page in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page])

        output_pdf = io.BytesIO()
        pdf_writer.write(output_pdf)
        output_pdf_bytes = output_pdf.getvalue()
        
        with open(path, 'wb') as output_file:
            output_file.write(output_pdf_bytes)
        return path

    except Exception as e:
        print(f"Erro ao converter PDF para DOCX: {e}")
        return None

def mergePdf(pdf_paths, output_path):
    """
    Merge multiple PDF files into one output file
    
    Args:
        pdf_paths (list): List of paths to PDF files to merge
        output_path (str): Path where the merged PDF will be saved
        
    Returns:
        str: Path to the merged PDF if successful, None otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a PDF merger object
        pdf_merger = PyPDF2.PdfMerger()
        
        # Add each PDF to the merger
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                pdf_merger.append(pdf_path)
            else:
                print(f"Arquivo não encontrado: {pdf_path}")
        
        # Write the merged PDF to the output path
        with open(output_path, 'wb') as output_file:
            pdf_merger.write(output_file)
        
        return output_path
    except Exception as e:
        print(f"Erro ao mesclar PDFs: {e}")
        return None