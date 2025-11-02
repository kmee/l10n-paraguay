Vou buscar informações sobre os modelos e campos que você mencionou no projeto para
criar um plano de desenvolvimento adequado.Com base nos campos do modelo que você copiou
para a localização do Paraguai, vou criar um plano de desenvolvimento estruturado para
implementar o módulo `l10n_py` no Odoo usando Git e Claude Code.

## **Plano de Desenvolvimento - Localização Paraguai (l10n_py)**

### **FASE 1: Estrutura Inicial do Repositório**

**Requisito 1.1 - Inicialização do Repositório Git**

- Criar repositório Git novo ou fazer fork do repositório Odoo existente
- Configurar branch principal: `main` ou `master`
- Criar branch de desenvolvimento: `dev-l10n-py`
- Configurar `.gitignore` para arquivos Python e Odoo

**Requisito 1.2 - Estrutura de Diretórios do Módulo**

```
l10n_py/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── account_chart_template_data.xml
│   ├── account.account.template.csv
│   ├── account.tax.group.csv
│   ├── account.tax.template.csv
│   └── fiscal_positions.xml
├── models/
│   ├── __init__.py
│   ├── account_move.py
│   ├── account_authorization.py
│   └── res_partner.py
├── views/
│   ├── account_move_views.xml
│   ├── account_authorization_views.xml
│   └── res_partner_views.xml
├── security/
│   └── ir.model.access.csv
├── static/
│   └── description/
│       └── icon.png
└── README.md
```

### **FASE 2: Implementação dos Modelos Base**

**Requisito 2.1 - Modelo de Autorização (Timbrado)**

- Criar modelo `account.authorization` com campos:
  - Número de timbrado
  - Data de início e fim de validade
  - Faixa de numeração autorizada
  - Estabelecimento e ponto de expedição
  - Tipo de documento

**Requisito 2.2 - Extensão do account.move** Implementar campos específicos do Paraguai
baseados no CSV:

- Campos de IVA:
  - `amount_iva_5` (IVA 5%)
  - `amount_iva_10` (IVA 10%)
  - `amount_iva_total` (Total IVA)
- Campos de subtotais:
  - `amount_subtotal_5`
  - `amount_subtotal_10`
  - `amount_subtotal_exempt`
- Campo `amount_total_words` (Total em letras)
- Campo `authorization_id` (link com timbrado)

**Requisito 2.3 - Modelo res.partner**

- Adicionar campo RUC (Registro Único de Contribuintes)
- Validação de formato RUC
- Campo para tipo de contribuinte

### **FASE 3: Configuração Fiscal**

**Requisito 3.1 - Plano de Contas**

- Criar estrutura de contas contábeis padrão do Paraguai
- Configurar códigos de contas conforme normativa local
- Definir contas de IVA (crédito e débito fiscal)

**Requisito 3.2 - Impostos**

- Configurar grupos de impostos:
  - IVA 10%
  - IVA 5%
  - Exento
- Criar templates de impostos com cálculos apropriados
- Configurar contas contábeis para cada imposto

**Requisito 3.3 - Posições Fiscais**

- Criar posições fiscais padrão
- Configurar mapeamento de impostos para operações internas
- Configurar mapeamento para exportação/importação

### **FASE 4: Interface de Usuário**

**Requisito 4.1 - Views de Faturas**

- Adicionar campos de IVA nas views de fatura
- Criar aba "Informações Fiscais Paraguai"
- Mostrar discriminação de impostos (5%, 10%, exento)
- Adicionar campo de timbrado obrigatório

**Requisito 4.2 - View de Autorização (Timbrado)**

- Criar menu de configuração para timbrados
- Formulário de criação/edição de timbrados
- Lista com status de validade (ativo/vencido)
- Alertas de vencimento próximo

**Requisito 4.3 - Relatórios**

- Personalizar layout de fatura conforme padrão paraguaio
- Incluir informações de timbrado
- Mostrar discriminação de IVA
- Total em letras (guaranis)

### **FASE 5: Lógica de Negócio**

**Requisito 5.1 - Validações**

- Validar número de fatura dentro da faixa autorizada
- Verificar validade do timbrado antes de confirmar fatura
- Validar formato de RUC
- Controlar sequência de numeração

**Requisito 5.2 - Cálculos Automáticos**

- Calcular automaticamente IVA 5% e 10%
- Separar base tributável por alíquota
- Converter total para texto em guaranis
- Calcular totais discriminados

**Requisito 5.3 - Integrações**

- Preparar estrutura para futura integração com SIFEN (quando aplicável)
- Exportação de dados para livros fiscais
- Geração de arquivos para declarações fiscais

### **FASE 6: Dados de Demonstração e Testes**

**Requisito 6.1 - Dados Demo**

- Criar empresas de exemplo com RUC válido
- Timbrados de exemplo
- Faturas de demonstração com diferentes alíquotas
- Clientes e fornecedores de exemplo

**Requisito 6.2 - Testes Unitários**

- Testes de validação de RUC
- Testes de cálculo de impostos
- Testes de numeração de faturas
- Testes de validade de timbrado

### **FASE 7: Documentação e Deploy**

**Requisito 7.1 - Documentação**

- README com instruções de instalação
- Documentação de configuração inicial
- Guia de uso para usuários finais
- Changelog com versões

**Requisito 7.2 - Controle de Versão**

- Criar tags para cada release
- Manter branch de produção estável
- Pull requests para revisão de código
- Commits atômicos e bem descritos

### **FLUXO GIT RECOMENDADO**

1. **Branch Strategy**:

   - `main`: versão estável em produção
   - `develop`: integração de features
   - `feature/[nome]`: desenvolvimento de funcionalidades
   - `hotfix/[nome]`: correções urgentes

2. **Padrão de Commits**:

   ```
   [TIPO] Descrição curta

   - Detalhes da mudança
   - Impacto no sistema
   ```

   Tipos: FEAT, FIX, DOC, STYLE, REFACTOR, TEST

3. **Processo de Release**:
   - Merge develop → main
   - Criar tag versionada (v1.0.0)
   - Gerar changelog
   - Atualizar versão no **manifest**.py

### **INSTRUÇÕES PARA CLAUDE CODE**

Envie este plano ao Claude Code com as seguintes orientações:

1. **Começar pela estrutura base** (Fase 1)
2. **Implementar modelos incrementalmente** (Fase 2)
3. **Usar os campos do CSV fornecido** como referência
4. **Commitar frequentemente** com mensagens descritivas
5. **Testar cada funcionalidade** antes de avançar
6. **Documentar o código** com docstrings Python
7. **Seguir convenções Odoo** para nomenclatura
8. **Criar branches específicas** para cada fase

Este plano fornece uma base sólida para desenvolver a localização paraguaia no Odoo, com
foco nos requisitos fiscais específicos do país e mantendo boas práticas de
desenvolvimento e controle de versão.
