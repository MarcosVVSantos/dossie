# Guia de Instalação - Dossiê v4

## Pré-requisitos

- Python 3.12 ou superior
- Git (opcional, para clonar o repositório)

## Instalação em Nova Máquina

### 1. Copiar o Projeto

Copie toda a pasta do projeto para a nova máquina ou clone do repositório.

### 2. Criar Ambiente Virtual (Recomendado)

```powershell
# Navegue até a pasta do projeto
cd caminho\para\dossiev4

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual
.\venv\Scripts\Activate.ps1
```

Se tiver erro de execução de scripts, execute como administrador:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependências

```powershell
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

**IMPORTANTE:** O arquivo `.env` já está configurado com **caminhos relativos** que funcionam em qualquer máquina.

Você só precisa verificar/atualizar as credenciais:

1. Abra o arquivo `.env` na raiz do projeto
2. Verifique as credenciais de acesso:
   ```dotenv
   email=marcos.santos@mottu.com.br
   password=mitu.2809
   ```
3. Os caminhos de arquivos já estão configurados como relativos:
   ```dotenv
   excel=src/utils/Relatório BOs.xlsx
   saida=src/output/gerador
   CONTRACT_PATH=src/output/gerador/contract
   ```

### 5. Verificar Estrutura de Pastas

Certifique-se de que as seguintes pastas existem:
- `src/output/gerador/document/`
- `src/output/gerador/cnh/`
- `src/output/gerador/crlv/`
- `src/output/gerador/contract/`
- `src/output/gerador/bo/`

O script criará a pasta `done/` automaticamente.

### 6. Preparar Arquivo Excel

Coloque o arquivo "Relatório BOs.xlsx" em: `src/utils/Relatório BOs.xlsx`

O arquivo Excel deve conter as colunas:
- `dataVehiclePlate` (obrigatório)
- `dataUserId` (obrigatório)
- `dataOccurrenceType` (obrigatório)

### 7. Executar o Script

```powershell
# Para merge de PDFs
python src/main/geracao/gerador/mergePDF.py

# Ou executar o main.py (se houver)
python main.py
```

## Problemas Comuns

### Erro: PermissionError [WinError 5]

**Causa:** Caminhos absolutos hardcoded no `.env`

**Solução:** Use sempre caminhos relativos no `.env`:
```dotenv
# ❌ ERRADO
excel=C:\Users\Usuario\Documents\projeto\arquivo.xlsx

# ✅ CORRETO
excel=src/utils/Relatório BOs.xlsx
```

### Erro: Arquivo Excel não encontrado

**Solução:** Certifique-se de que o arquivo está em `src/utils/Relatório BOs.xlsx` relativo à raiz do projeto.

### Erro: Módulos não encontrados

**Solução:** Instale as dependências:
```powershell
pip install -r requirements.txt
```

### Erro: Script não encontra .env

**Solução:** O `.env` deve estar na raiz do projeto (mesma pasta que `main.py` e `readme.md`)

## Estrutura de Diretórios Esperada

```
dossiev4/
├── .env                          # Configurações (caminhos relativos!)
├── .env.example                  # Exemplo de configuração
├── main.py
├── readme.md
├── requirements.txt
├── INSTALACAO.md                 # Este arquivo
├── src/
│   ├── main/
│   │   └── geracao/
│   │       ├── coletas/
│   │       └── gerador/
│   │           ├── mergePDF.py
│   │           └── generatePDF.py
│   ├── output/
│   │   └── gerador/
│   │       ├── document/         # PDFs de documentos gerados
│   │       ├── cnh/              # PDFs de CNH
│   │       ├── crlv/             # PDFs de CRLV
│   │       ├── contract/         # PDFs de contratos
│   │       ├── bo/               # PDFs de BOs
│   │       └── done/             # Resultado final (criado automaticamente)
│   ├── settings/
│   │   ├── config.py
│   │   └── env_loader.py
│   └── utils/
│       └── Relatório BOs.xlsx    # Arquivo de entrada
└── tests/
```

## Checklist de Instalação

- [ ] Python 3.12+ instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` configurado (caminhos relativos)
- [ ] Credenciais corretas no `.env`
- [ ] Arquivo Excel em `src/utils/Relatório BOs.xlsx`
- [ ] PDFs de entrada nas pastas corretas
- [ ] Primeiro teste executado com sucesso

## Suporte

Para problemas, verifique:
1. Logs de erro completos
2. Caminhos no `.env` (devem ser relativos)
3. Estrutura de pastas
4. Permissões de leitura/escrita nas pastas de saída
