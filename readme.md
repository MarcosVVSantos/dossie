# 📋 Dossie v4 - Sistema de Geração de Dossiês de Boletins de Ocorrência

Sistema automatizado para geração de dossiês completos de Boletins de Ocorrência, incluindo coleta de documentos (CNH, CRLV, Contratos, BOs) e geração de PDFs finais mesclados.

## 📑 Índice

- [Funcionalidades](#-funcionalidades)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Fluxo de Execução](#-fluxo-de-execução)
- [Troubleshooting](#-troubleshooting)

## 🚀 Funcionalidades

- ✅ Download automático de Boletins de Ocorrência
- ✅ Coleta de CNH (Carteira Nacional de Habilitação)
- ✅ Coleta de Contratos de Locação
- ✅ Coleta de CRLV (Documento do Veículo)
- ✅ Geração de PDF customizado com dados do BO
- ✅ Merge automático de todos os documentos em dossiê único
- ✅ Organização por tipo de ocorrência
- ✅ Validação de documentos completos
- ✅ Limpeza automática apenas da pasta `done`

## 📋 Pré-requisitos

### Software Necessário

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **Git** (opcional, para clonar o repositório)

### Bibliotecas Python

```bash
pandas
openpyxl
requests
PyPDF2
fpdf
pillow
python-dotenv
```

## 🔧 Instalação

### 1. Clone ou baixe o projeto

```bash
git clone <url-do-repositorio>
cd dossiev4
```

Ou baixe e extraia o arquivo ZIP do projeto.

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

Se o arquivo `requirements.txt` não existir, instale manualmente:

```bash
pip install pandas openpyxl requests PyPDF2 fpdf pillow python-dotenv
```

### 3. Configure o arquivo `.env`

Copie o arquivo `.env.example` (se existir) ou crie um novo `.env` na raiz do projeto:

```env
# URLs das APIs
auth_url=https://sso.mottu.cloud/realms/Internal/protocol/openid-connect/token
loginUrl=https://sso.mottu.cloud/realms/Internal/protocol/openid-connect/token
backendUrl=https://backend.mottu.cloud/api/v2
operationUrl=https://operation-backend.mottu.cloud/api/v2
paymentsUrl=https://payments-backend.mottu.cloud/api/v2
imageProcessUrl=https://image-process.mottu.cloud/api
fileToolsUrl=https://file-tools.mottu.cloud/api
geopifyUrl=https://api.geoapify.com/v1/geocode/
boUrlTemplate=https://operation-backend.mottu.cloud/api/v2/Veiculo/BuscarDetalheVeiculoAnexos/{}/{}

# Credenciais de autenticação
email=seu.email@mottu.com.br
password=sua_senha
client_id=mottu-admin
grant_type=password

# Chave da API Geopify
geopify=sua_chave_geopify

# Caminhos (Use SEMPRE caminhos relativos ao diretório raiz do projeto)
excel=src/utils/Relatório BOs.xlsx
saida=src/output/gerador/cnh
CONTRACT_PATH=src/output/gerador/contract
CRLV_PATH=src/output/gerador/crlv
boOutputPath=src/output/gerador/bo

# Dados da Mottu
MOTTU_CNPJ=17.182.260/0001-08
MOTTU_ADDRESS=Av. Dr. Gastão Vidigal, 501 - Vila Leopoldina, São Paulo - SP, 05314-000
MOTTU_PHONE=(11) 3181-8188

# Configurações
excelPage=Página1
maxRetries=3
backoff=5
```

### 4. Prepare o arquivo Excel

Coloque o arquivo `Relatório BOs.xlsx` na pasta `src/utils/` com as seguintes colunas obrigatórias:

- `dataOccurrenceType` - Tipo da ocorrência (1-11)
- `dataVehicleId` - ID do veículo
- `dataVehiclePlate` - Placa do veículo
- `dataUserId` - ID do usuário/locatário
- `dataUserRentalId` - ID do aluguel (alternativa ao dataUserId)

**⚠️ Importante:** O sistema usa caminhos relativos, portanto não é necessário configurar caminhos absolutos no `.env`. Todos os caminhos são relativos ao diretório raiz do projeto.

## 🎯 Como Usar

### Execução Completa (Recomendado)

Execute o script principal que roda todos os módulos na ordem correta:

```bash
python main.py
```

### Execução Individual de Módulos

Se necessário, você pode executar módulos individualmente:

```bash
# 1. Download de BOs
python src/main/geracao/coletas/bo_download.py

# 2. Coleta de CNHs
python src/main/geracao/coletas/driverLicense.py

# 3. Coleta de Contratos
python src/main/geracao/coletas/rentalDocument.py

# 4. Coleta de CRLVs
python src/main/geracao/coletas/vehicleDocument.py

# 5. Geração de PDFs
python src/main/geracao/gerador/generatePDF.py

# 6. Merge final
python src/main/geracao/gerador/mergePDF.py
```

## 📁 Estrutura do Projeto

```
dossiev4/
├── main.py                          # Script principal (executa todos os módulos)
├── .env                             # Configurações e credenciais
├── README.md                        # Este arquivo
├── requirements.txt                 # Dependências Python
│
├── src/
│   ├── main/
│   │   └── geracao/
│   │       ├── coletas/
│   │       │   ├── bo_download.py          # Download de BOs
│   │       │   ├── driverLicense.py        # Coleta de CNHs
│   │       │   ├── rentalDocument.py       # Coleta de Contratos
│   │       │   └── vehicleDocument.py      # Coleta de CRLVs
│   │       │
│   │       └── gerador/
│   │           ├── generatePDF.py          # Gera PDF do BO
│   │           └── mergePDF.py             # Mescla todos os PDFs
│   │
│   ├── settings/
│   │   ├── auth.py                  # Gerenciamento de autenticação
│   │   ├── config.py                # Configurações centralizadas
│   │   ├── env_loader.py            # Carregador de .env
│   │   └── http.py                  # Utilitários HTTP
│   │
│   ├── utils/
│   │   ├── fileUtils.py             # Utilitários de arquivo
│   │   ├── documentUtils.py         # Utilitários de documento
│   │   ├── template.html            # Template HTML
│   │   ├── logo.png                 # Logo da Mottu
│   │   └── Relatório BOs.xlsx       # Arquivo Excel de entrada
│   │
│   └── output/
│       └── gerador/
│           ├── bo/                  # BOs baixados
│           ├── cnh/                 # CNHs coletadas
│           ├── contract/            # Contratos coletados
│           ├── crlv/                # CRLVs coletados
│           ├── document/            # PDFs gerados
│           └── done/                # Dossiês finais mesclados ✅
│
└── tests/                           # Testes (opcional)
```

## ⚙️ Fluxo de Execução

### Ordem de Execução do `main.py`

1. **🧹 Limpeza da pasta `done`**
   - Remove apenas os dossiês finais da pasta `src/output/gerador/done`
   - ⚠️ **Não limpa** as demais pastas (bo, cnh, contract, crlv, document)

2. **📥 Download de Boletins de Ocorrência** (`bo_download.py`)
   - Busca dados do BO via API
   - Baixa anexos do BO
   - Converte imagens para PDF se necessário
   - Salva em: `src/output/gerador/bo/`

3. **🪪 Coleta de CNH** (`driverLicense.py`)
   - Busca CNH do usuário via API
   - Baixa e converte para PDF
   - Salva em: `src/output/gerador/cnh/PLACA_USERID.pdf`

4. **📝 Coleta de Contrato** (`rentalDocument.py`)
   - Gera contrato via API
   - Baixa PDF do contrato
   - Salva em: `src/output/gerador/contract/PLACA_USERID.pdf`

5. **🚗 Coleta de CRLV** (`vehicleDocument.py`)
   - Busca documento do veículo via API
   - Baixa PDF do CRLV
   - Salva em: `src/output/gerador/crlv/PLACA_USERID.pdf`

6. **📄 Geração de PDF Final** (`generatePDF.py`)
   - Lê dados do Excel
   - Gera PDF customizado com informações do BO
   - Salva em: `src/output/gerador/document/PLACA_USERID.pdf`

7. **🔄 Merge de PDFs** (`mergePDF.py`)
   - Lê mapeamento do Excel
   - Valida conjuntos completos de documentos
   - Mescla na ordem correta:
     1. Documento Gerado
     2. CNH
     3. CRLV
     4. Contrato (exceto tipos 4 e 10)
     5. BO (apenas tipos 6, 7, 8, 9, 10)
   - Organiza por tipo de ocorrência
   - Salva em: `src/output/gerador/done/TIPO_DATA/`

### Tipos de Ocorrência

| Tipo | Descrição | Documentos Incluídos |
|------|-----------|---------------------|
| 1 | Registro de BO - Roubo | Documento + CNH + CRLV + Contrato |
| 2 | Registro de BO - Inventário | Documento + CNH + CRLV + Contrato |
| 3 | Registro de BO - Furto | Documento + CNH + CRLV + Contrato |
| 4 | Registro de BO - Violação | Documento + CNH + CRLV (SEM Contrato) |
| 5 | Registro de BO - Apropriação Indébita | Documento + CNH + CRLV + Contrato |
| 6 | Registro de BO - Veículo Encontrado | Documento + CNH + CRLV + Contrato + BO |
| 7 | Baixa de BO - Veículo Recuperado | Documento + CNH + CRLV + Contrato + BO |
| 8 | Baixa de BO - Veículo Apreendido | Documento + CNH + CRLV + Contrato + BO |
| 9 | Baixa de BO - Veículo Apreendido BO Ativo | Documento + CNH + CRLV + Contrato + BO |
| 10 | Alteração de BO - Roubo/Furto | Documento + CNH + CRLV + BO (SEM Contrato) |
| 11 | Não Criminal - Outros | Documento + CRLV |

## 🔍 Troubleshooting

### ❌ Erro: "ModuleNotFoundError: No module named 'src'"

**Solução:** Execute sempre da raiz do projeto:
```bash
cd C:\Users\Seu Nome\Documents\scripts\dossiev4\dossiev4
python main.py
```

### ❌ Erro: "Falha ao obter token. Abortando..."

**Causas possíveis:**
1. Credenciais incorretas no `.env`
2. URL de autenticação errada
3. Problemas de rede

**Solução:** Verifique as credenciais no arquivo `.env`

### ❌ Erro: "Arquivo Excel não encontrado"

**Solução:** 
1. Verifique o caminho no `.env`
2. Certifique-se que o arquivo existe em `src/utils/Relatório BOs.xlsx`

### ❌ Erro: "CNH não encontrada na pasta"

**Solução:**
1. Execute primeiro o `driverLicense.py`
2. Verifique se o arquivo foi salvo em `src/output/gerador/cnh/`
3. O arquivo deve seguir o padrão `PLACA_USERID.pdf`

### ⚠️ Warning: "Logo não encontrada"

**Impacto:** Os PDFs serão gerados sem logo
**Solução:** Coloque o arquivo `logo.png` em `src/utils/`

### ❌ Conjuntos incompletos no merge

**Solução:**
1. Verifique se todos os scripts anteriores foram executados
2. Confirme que os arquivos existem nas pastas corretas
3. Verifique os logs para identificar qual documento está faltando

## 📊 Logs e Monitoramento

Durante a execução, o sistema exibe:
- ✅ Operações bem-sucedidas
- ⚠️ Avisos (conjuntos incompletos, documentos faltando)
- ❌ Erros críticos
- 📊 Estatísticas finais

## 🔐 Segurança

⚠️ **IMPORTANTE:**
- Nunca commite o arquivo `.env` com credenciais reais
- Use variáveis de ambiente em produção
- Mantenha backups dos arquivos gerados

## 📞 Suporte

Em caso de dúvidas ou problemas, consulte:
1. Este README
2. Logs de execução
3. Seção Troubleshooting
4. Equipe responsável pelo projeto

---

**Versão:** 4.0  
**Última atualização:** Janeiro 2026
