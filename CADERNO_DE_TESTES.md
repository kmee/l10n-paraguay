# Caderno de Testes Manual - l10n-paraguay (Odoo 16)

> Validação manual ponta-a-ponta da localização paraguaia e regime de maquila. Execute
> cada teste na interface web do Odoo e marque `[x]` quando concluído.

---

## 1. Pré-requisitos

- [ ] Odoo 16 rodando com dados demo carregados
- [ ] Módulos instalados:

| Módulo                   | Instalado? |
| ------------------------ | ---------- |
| `l10n_py`                | [ ]        |
| `l10n_py_base`           | [ ]        |
| `l10n_py_account`        | [ ]        |
| `l10n_py_edi_base`       | [ ]        |
| `l10n_py_edi_sifen`      | [ ]        |
| `l10n_py_maquila_base`   | [ ]        |
| `l10n_py_maquila_ops`    | [ ]        |
| `l10n_py_maquila_mrp`    | [ ]        |
| `l10n_py_maquila_report` | [ ]        |

---

## 2. l10n_py - Plano de Contas

**Caminho:** Faturamento > Configuração > Contabilidade > Plano de Contas

- [ ] Template "Paraguay" carregado
- [ ] Contas contábeis com códigos numéricos paraguaios
- [ ] Grupo **IVA 10%** existe
- [ ] Grupo **IVA 5%** existe
- [ ] Grupo **Exento** existe
- [ ] Impostos de venda: IVA 10%, IVA 5%, Exento
- [ ] Impostos de compra: IVA 10%, IVA 5%, Exento
- [ ] Posições fiscais configuradas para Paraguay

---

## 3. l10n_py_base - Dados Geográficos & RUC

### 3.1 Departamentos

**Caminho:** Contatos > Configuração > Localizações > Estados > filtrar "Paraguay"

- [ ] 17 departamentos + Asunción

### 3.2 Cidades e Bairros

- [ ] Cidades paraguaias com `l10n_py_code`
- [ ] Bairros vinculados a cidades

### 3.3 Validação RUC

**Caminho:** Contatos > Criar contato empresa

- **Tipo identificação:** RUC
- **Número:** `80012345`

- [ ] DV calculado automaticamente: `80012345-6`
- [ ] Tipo Contribuyente auto-preenche

### 3.4 Validação CI (No Contribuyente)

- **Tipo identificação:** CI
- **Número:** `1234567`

- [ ] Tipo Contribuyente = "No Contribuyente"
- [ ] Campo RUC vazio

---

## 4. l10n_py_account - Timbrados & Faturamento

### 4.1 Timbrados Demo

**Caminho:** Faturamento > Configuração > Timbrados

- [ ] 6 timbrados demo existem (valid/to_expire/expired)
- [ ] Estados calculados corretamente

### 4.2 Fatura IVA 10%

- **Cliente:** Comercial Guaraní SA
- **Linha:** Notebook Dell Inspiron — Qtd: 2 — ₲ 5.500.000 — IVA 10%

- [ ] Confirmar → número `001-001-NNNNNNN`
- [ ] Campos SIFEN: Base 10%, IVA 10%, Total

### 4.3 Fatura IVA 5%

- [ ] IVA 5% calculado corretamente (F004, F015, F018)

### 4.4 Fatura Mista (10% + 5% + Exento)

- [ ] F008 = F003 + F004 + F005
- [ ] IVA total = IVA 10% + IVA 5%

### 4.5 Fatura Moeda Estrangeira

- [ ] Total PYG (F023) = total × taxa de câmbio

---

## 5. l10n_py_edi_base - Documentos Eletrônicos

### 5.1 Tipos DTE

- [ ] FE (1), AFE (4), NCE (5), NDE (6), NRE (7) existem

### 5.2 Status EDI em Faturas

- [ ] Campo Status EDI visível
- [ ] Tipo emissão, transação, presença funcionam

### 5.3 NCE com Documentos Associados

- [ ] Tipo 1 (Electrónico): CDC 44 dígitos
- [ ] Tipo 2 (Impreso): timbrado + est + ponto + número
- [ ] Tipo 3 (Constancia): tipo + número
- [ ] Constraints exclusivas funcionam

### 5.4 Inutilização de Números

- [ ] Range máximo 1000
- [ ] Dentro do range do timbrado
- [ ] Não pode inutilizar números usados

---

## 6. Conectores EDI

**Caminho:** Menu técnico > `l10n_py.edi.connector`

- [ ] Opção SIFEN Directo (se `l10n_py_edi_sifen` instalado)
- [ ] Constraint: 1 conector por empresa
- [ ] Campos de certificado digital na empresa (SIFEN)

---

## 7. Maquila Base - Programas

### 7.1 Menu Maquila

**Caminho:** Menu principal > Maquila

- [ ] Menu **Maquila** visível no topo
- [ ] Subitens: Dashboard, Programs, Operations, Manufacturing, Fiscal, Reports,
      Configuration
- [ ] Dashboard é o primeiro item (kanban de programas ativos)

### 7.2 Programas Demo

**Caminho:** Maquila > Programs

| Programa                         | Tipo      | Estado | Matriz           |
| -------------------------------- | --------- | ------ | ---------------- |
| Chicotes Eléctricos Automotrices | Pura      | Active | AutoParts Brasil |
| Paneles Plásticos Interiores     | Ociosidad | Active | TechParts USA    |
| Componentes Electrónicos         | Servicio  | Draft  | AutoParts Brasil |

- [ ] 3 programas existem com estados corretos
- [ ] Filtro padrão mostra programas ativos

### 7.3 Formulário do Programa

**Caminho:** Abrir programa "Chicotes Eléctricos"

- [ ] **Stat buttons** visíveis: Admissions, Exports, Guarantees, BOMs, Productions,
      Waste, CNIME Reports
- [ ] **Aba Products:** 1 produto (Chicote Eléctrico) com certificado INTN
- [ ] **Aba Operations:** admissões, exportações, garantias em tabelas full-width
- [ ] **Aba Manufacturing:** BOMs e waste em tabelas full-width
- [ ] **Aba Contracts:** agreement CNIME vinculado
- [ ] **Aba Documents:** campo para PDF da resolução
- [ ] **Chatter** com followers e atividades
- [ ] **Statusbar:** draft → active → closed

### 7.4 Workflow do Programa

- [ ] Botão "Activate" (draft → active)
- [ ] Botão "Suspend" (active → suspended)
- [ ] Botão "Close" (active/suspended → closed)
- [ ] Botão "Reset to Draft"

### 7.5 Programa Ociosidad

**Caminho:** Abrir programa "Paneles Plásticos"

- [ ] `internal_sale_pct` = 20.0%
- [ ] Tipo = Capacidad Ociosa

### 7.6 Empresa Maquiladora

**Caminho:** Configurações > Empresas > editar empresa principal

- [ ] Campo `l10n_py_is_maquiladora` = True

---

## 8. Maquila Ops - Operações

### 8.1 Admissões

**Caminho:** Maquila > Operations > Admissions

| Despacho      | Programa  | Estado        | CIF    |
| ------------- | --------- | ------------- | ------ |
| DI-2026-00101 | Chicotes  | Admitted      | 55.000 |
| DI-2026-00102 | Chicotes  | In Production | 42.000 |
| DI-2026-00201 | Plásticos | Draft         | 28.000 |

- [ ] 3 admissões existem
- [ ] Deadline calculado (+12 meses da data de admissão)
- [ ] Linhas com produto, lote, quantidade, NCM, FOB

### 8.2 Workflow Admissão

**Caminho:** Abrir admissão DI-2026-00201 (draft)

- [ ] Botão "Admit" → exige certificado CNIME (erro se vazio)
- [ ] Preencher certificado → "Admit" funciona
- [ ] Botão "In Production" → muda estado
- [ ] Botão "Close"

### 8.3 Exportações

**Caminho:** Maquila > Operations > Exports

| Despacho      | Programa  | Estado     | Incoterm |
| ------------- | --------- | ---------- | -------- |
| DE-2026-00101 | Chicotes  | Dispatched | FOB      |
| DE-2026-00102 | Chicotes  | Confirmed  | CIF      |
| DE-2026-00201 | Plásticos | Draft      | FOB      |

- [ ] 3 exportações existem
- [ ] DE-2026-00101 tem admission_ids vinculada (rastreabilidade)
- [ ] DE-2026-00102 tem 2 admissões vinculadas

### 8.4 Workflow Exportação

- [ ] Confirm exige pelo menos 1 admissão vinculada
- [ ] Dispatch funciona

### 8.5 Garantias

**Caminho:** Maquila > Operations > Guarantees

| Nome                       | Tipo      | Valor   | Programa  |
| -------------------------- | --------- | ------- | --------- |
| Fianza Bancaria - Regional | Bank      | 200.000 | Chicotes  |
| Póliza Seguro - Mapfre     | Insurance | 100.000 | Chicotes  |
| Fianza Bancaria - BBVA     | Bank      | 150.000 | Plásticos |

- [ ] 3 garantias existem
- [ ] `amount_used` calculado (soma CIF admissões ativas)
- [ ] `amount_available` = amount - amount_used

### 8.6 Posições Fiscais Maquila

**Caminho:** Faturamento > Configuração > Posições Fiscais

- [ ] "Maquila - Admisión Temporaria" existe
- [ ] "Maquila - Exportación Exenta" existe

### 8.7 Stock Locations

**Caminho:** Inventário > Configuração > Armazéns > Localizações

- [ ] Maquila > Admisión Temporaria
- [ ] Maquila > Producción
- [ ] Maquila > Terminado
- [ ] Maquila > Residuos

### 8.8 Wizards Fiscais

**Caminho:** Maquila > Fiscal > TUM Calculation

- [ ] Wizard abre com campos: programa, período, VAN, export invoices
- [ ] Campos debit/credit account existem
- [ ] Botão "Compute" calcula valores
- [ ] Botão "Generate Entry" gera account.move (requer contas preenchidas)

**Caminho:** Maquila > Fiscal > Tax Credit (IVA)

- [ ] Wizard com action_type (compensate/transfer)
- [ ] Transfer mostra campo partner
- [ ] Campos debit/credit account existem

---

## 9. Maquila MRP - Produção

### 9.1 BOMs

**Caminho:** Maquila > Manufacturing > Bills of Materials

| BOM         | Produto           | Programa  | INTN |
| ----------- | ----------------- | --------- | ---- |
| BOM-CHE-001 | Chicote Eléctrico | Chicotes  | Sim  |
| BOM-PPI-001 | Panel Plástico    | Plásticos | Sim  |

- [ ] 2 BOMs existem com programa maquila vinculado
- [ ] BOM-CHE-001 tem 6 linhas (4 imported + 2 national)
- [ ] BOM-PPI-001 tem 3 linhas

### 9.2 Coeficientes INTN nas BOM Lines

**Caminho:** Abrir BOM-CHE-001 > linhas

| Componente     | Qty (gross) | Qty Net | Loss % | Origem              | País |
| -------------- | ----------- | ------- | ------ | ------------------- | ---- |
| Polímero ABS   | 1.05        | 1.00    | 4.76   | Temporary Admission | CN   |
| Aditivo UV     | 0.05        | 0.048   | 4.0    | Temporary Admission | DE   |
| Conector 12pin | 2           | 2       | 0      | Temporary Admission | CN   |
| Cable Cobre    | 3.5         | 3.2     | 8.57   | Temporary Admission | DE   |
| Tornillos M4   | 10          | —       | —      | National (PY)       | PY   |
| Cinta Aislante | 0.5         | —       | —      | National (PY)       | PY   |

- [ ] Campos `l10n_py_origin_type` e `l10n_py_origin_country` visíveis
- [ ] Campos OCA `product_qty_net` e `loss_percentage` presentes
- [ ] Certificado INTN no cabeçalho da BOM

### 9.3 Waste (Resíduos)

**Caminho:** Maquila > Manufacturing > Waste

| Produto      | Qty | Tipo      | Destino         | Estado     |
| ------------ | --- | --------- | --------------- | ---------- |
| Polímero ABS | 150 | Scrap     | Destruction     | Pending    |
| Cable Cobre  | 500 | Scrap     | Nationalization | In Process |
| Conector 12  | 25  | Defective | Re-export       | Completed  |
| Polímero ABS | 80  | Byproduct | Destruction     | Pending    |

- [ ] 4 registros de waste existem
- [ ] Campo `date` preenchido
- [ ] Workflow: pending → in_process → completed
- [ ] Campo `seam_approval` no waste de byproduct (DICT-SEAM-2026-001)

### 9.4 VAN Wizard

**Caminho:** Maquila > Manufacturing > VAN Calculation

- [ ] Wizard abre com programa e período
- [ ] Botão "Compute" busca dados de analytic lines
- [ ] Campos: total_cost, national_cost, mercosul_cost, imported_cost
- [ ] VAN % e Mercosul Content % calculados

---

## 10. Maquila Report - Relatórios

### 10.1 CNIME Reports

**Caminho:** Maquila > Reports > CNIME Reports

| Programa  | Período  | Estado    | Emprego |
| --------- | -------- | --------- | ------- |
| Chicotes  | Feb 2026 | Submitted | 180     |
| Chicotes  | Mar 2026 | Generated | 185     |
| Plásticos | Mar 2026 | Draft     | 45      |

- [ ] 3 reports existem
- [ ] Report submetido tem `submission_date` e `submission_protocol`
- [ ] Botões: Generate → Validate → Submit
- [ ] Botão "Generate SIMEX Payload" visível em validated/submitted

### 10.2 Dashboard

**Caminho:** Maquila > Dashboard

- [ ] View kanban com programas ativos
- [ ] Cards mostram: nome, código, tipo, estado, matriz, vencimento
- [ ] Badge de estado com cores (active=verde, suspended=amarelo)

### 10.3 Extensão EDI (SIFEN)

**Caminho:** Criar fatura de venda para programa maquila, preview XML

- [ ] Observação contém "Producto Maquila - Ley 1064/97 - RES-BIM-2026-001"

---

## 11. Integrações Cross-Module

### 11.1 Programa como Hub Central

**Caminho:** Abrir programa "Chicotes Eléctricos"

- [ ] Stat button Admissions mostra "2" → clique abre lista filtrada
- [ ] Stat button Exports mostra "2" → clique abre lista filtrada
- [ ] Stat button Guarantees mostra "2" → clique abre lista filtrada
- [ ] Stat button BOMs mostra "1" → clique abre lista filtrada
- [ ] Stat button Waste mostra "3" → clique abre lista filtrada
- [ ] Stat button CNIME Reports mostra "2" → clique abre lista filtrada

### 11.2 Programa Plásticos

- [ ] Stat button Admissions mostra "1"
- [ ] Stat button Guarantees mostra "1"
- [ ] Stat button BOMs mostra "1"
- [ ] Stat button Waste mostra "1"
- [ ] Stat button CNIME Reports mostra "1"

### 11.3 Purchase/Sale com Programa

**Caminho:** Compras > Ordens de Compra > Criar

- [ ] Campo `l10n_py_maquila_program_id` visível
- [ ] Ao selecionar programa, posição fiscal auto-preenche (admissão temporária)

**Caminho:** Vendas > Ordens de Venda > Criar

- [ ] Campo `l10n_py_maquila_program_id` visível
- [ ] Ao selecionar programa, posição fiscal auto-preenche (exportação exenta)
- [ ] Maquila pura + cliente paraguaio → bloqueio na confirmação

---

## 12. Resumo de Execução

**Data:** **_/_**/**\_\_** **Executor:**
**\*\***\*\***\*\***\_\_\_\_**\*\***\*\***\*\*** **Ambiente:**
**\*\***\*\***\*\***\_\_\_\_**\*\***\*\***\*\***

| #   | Seção                       | Testes  | OK  | FAIL | SKIP |
| --- | --------------------------- | ------- | --- | ---- | ---- |
| 2   | Plano de Contas             | 8       |     |      |      |
| 3   | Dados Geográficos & RUC     | 6       |     |      |      |
| 4   | Timbrados & Faturamento     | 8       |     |      |      |
| 5   | Documentos Eletrônicos      | 8       |     |      |      |
| 6   | Conectores EDI              | 3       |     |      |      |
| 7   | Maquila Base - Programas    | 15      |     |      |      |
| 8   | Maquila Ops - Operações     | 20      |     |      |      |
| 9   | Maquila MRP - Produção      | 12      |     |      |      |
| 10  | Maquila Report - Relatórios | 8       |     |      |      |
| 11  | Integrações Cross-Module    | 10      |     |      |      |
|     | **TOTAL**                   | **~98** |     |      |      |

### Aprovação

- [ ] Todos os testes passaram
- [ ] Bugs registrados como issues
- [ ] Módulos prontos para uso

**Assinatura:** **\*\***\*\***\*\***\_\_\_\_**\*\***\*\***\*\***
