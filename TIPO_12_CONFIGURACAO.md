# 📋 Configuração do Tipo 12 - VEÍCULO ENCONTRADO SEM LOCAÇÃO

## Resumo das Alterações Realizadas

O tipo 12 (VEÍCULO ENCONTRADO SEM LOCAÇÃO) foi configurado para funcionar sem contrato e sem CNH, precisando apenas de:
- ✅ Documento gerado (PDF com histórico)
- ✅ CRLV (documento do veículo)

## Alterações por Script

### 1. **generatePDF.py** ✅
**Arquivo:** `src/main/geracao/gerador/generatePDF.py`

**O que foi feito:**
- Adicionado caso `occurrence_type == 12` com texto específico
- Adicionado mapeamento de nome: `"BAIXA DE BOLETIM DE OCORRÊNCIA - VEÍCULO ENCONTRADO SEM LOCAÇÃO"`

**Texto gerado para tipo 12:**
```
No dia [data] e hora [hora], o rastreador do veiculo voltou a emitir sinais com a sua localização nas coordenadas: ([coordenadas]).
Deste modo, para averiguação dos sinais transmitidos foi enviado um prestador ao local. 
O motorista [nome] foi designado para a tarefa. 
Ao chegar ao local, confirmou a presença do veiculo da placa: [PLACA], e chassi: [CHASSI], abandonado e procedeu com a sua recolha. 
O veiculo foi encaminhado para o pátio da empresa para as devidas providências legais e contato.
```

---

### 2. **rentalDocument.py** ✅
**Arquivo:** `src/main/geracao/coletas/rentalDocument.py`

**O que foi feito:**
- Adicionado filtro para **pular tipo 12** durante coleta de contratos
- Lê coluna `dataOccurrenceType` do Excel
- Se tipo == 12, pula o registro com mensagem: `"⏭️  Pulando contrato para tipo 12..."`

**Impacto:** Evita erro de tentativa de processar contrato com dados vazios ("-")

---

### 3. **driverLicense.py** ✅
**Arquivo:** `src/main/geracao/coletas/driverLicense.py`

**O que foi feito:**
- Adicionado filtro para **pular tipo 12** durante coleta de CNH
- Lê coluna `dataOccurrenceType` do Excel
- Se tipo == 12, pula o registro com mensagem: `"⏭️  Pulando CNH para tipo 12..."`

**Impacto:** Evita processamento desnecessário de CNH para tipo 12

---

### 4. **vehicleDocument.py** ✅
**Arquivo:** `src/main/geracao/coletas/vehicleDocument.py`

**O que foi feito:**
- ✅ Sem alterações (processa TODOS os veículos, incluindo tipo 12)

**Impacto:** CRLV é coletado normalmente para tipo 12

---

### 5. **bo_download.py** ✅
**Arquivo:** `src/main/geracao/coletas/bo_download.py`

**O que foi feito:**
- ✅ Sem alterações necessárias (tipo 12 não está no mapeamento `ocorrencia_para_bo`)

**Impacto:** BO não é processado para tipo 12 (correto)

---

### 6. **mergePDF.py** ✅
**Arquivo:** `src/main/geracao/gerador/mergePDF.py`

**O que foi feito:**
- Tipo 12 adicionado à função `get_documentos_obrigatorios()`: retorna `["DOCUMENTO_GERADO", "CRLV"]`
- Tipo 12 adicionado à função `get_ordem_documentos()`: ordena como `[DOCUMENTO_GERADO, CRLV]`
- Tipo 12 adicionado ao mapeamento `tipo_documento_map`: `"BAIXA_DE_BOLETIM_DE_OCORRENCIA_VEICULO_ENCONTRADO_SEM_LOCACAO"`

**Impacto:** Merge gera dossiê apenas com documento + CRLV, sem contrato

---

## Fluxo de Execução para Tipo 12

```
┌─────────────────────────────────────────────────────────┐
│ main.py (sequência de execução)                         │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
  bo_download.py    driverLicense.py    rentalDocument.py
  (tipo 12: NÃO)    (tipo 12: PULA)     (tipo 12: PULA)
       │                  │                    │
       └──────────────────┼────────────────────┘
                          │
                          ▼
                vehicleDocument.py
              (tipo 12: PROCESSA CRLV)
                          │
                          ▼
                  generatePDF.py
              (tipo 12: GERA DOCUMENTO)
                          │
                          ▼
                    mergePDF.py
         (tipo 12: MERGES DOC + CRLV)
                          │
                          ▼
         RESULTADO: Dossiê completo (DOC + CRLV)
```

---

## Configuração Necessária no Excel

O arquivo `Relatório BOs.xlsx` deve conter:

| Coluna | Tipo 12 | Valor Exemplo |
|--------|---------|---------------|
| `dataOccurrenceType` | ✅ Obrigatório | `12` |
| `dataVehiclePlate` | ✅ Obrigatório | `ABC-1234` |
| `dataVehicleId` | ✅ Obrigatório | `12345` |
| `dataUserId` | ❌ Pode ser "-" | `-` |
| `dataUserRentalId` | ❌ Pode ser "-" | `-` |
| `dataOccurrenceBranchDriverName` | ✅ Obrigatório | `João Silva` |
| `dataVehicleChassis` | ✅ Obrigatório | `XXXXXX123456789` |
| `dataTrackingGeolocation` | ✅ Obrigatório | `-23.5505, -46.6333` |

---

## Checklist de Implementação

- [x] Tipo 12 adicionado em `generatePDF.py` com texto específico
- [x] Tipo 12 adicionado em mapeamento de nomes (generatePDF.py e mergePDF.py)
- [x] Filtro tipo 12 adicionado em `rentalDocument.py` (pula contrato)
- [x] Filtro tipo 12 adicionado em `driverLicense.py` (pula CNH)
- [x] Tipo 12 configurado em `mergePDF.py` (sem contrato, apenas doc + CRLV)
- [x] `vehicleDocument.py` processa CRLV normalmente para tipo 12
- [x] `bo_download.py` não processa tipo 12 (correto)
- [x] Ordem de execução em `main.py` está correta

---

## Como Testar

1. Adicione um registro com `dataOccurrenceType = 12` no Excel
2. Execute: `python main.py`
3. Verifique logs para mensagens como:
   - `⏭️  Pulando contrato para tipo 12...`
   - `⏭️  Pulando CNH para tipo 12...`
   - `✅ Conjunto completo encontrado para: [PLACA]_[USERID] - Tipo: 12`
4. Verifique pasta `src/output/gerador/done/` para dossiê gerado
5. Abra PDF e verifique se contém apenas: Documento + CRLV

---

## Status: ✅ COMPLETO

Tipo 12 está totalmente configurado e funcional em todos os scripts.
