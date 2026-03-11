# PRD — Tarefas Pendentes: l10n-paraguay (SIFEN)

> Gerado a partir do gap analysis PRD vs módulos implementados. Cada seção contém
> especificações BDD (Gherkin) prontas para implementação.

---

## 1. Gap Analysis Resumido

| RF    | Descrição                          | % Impl. | Pendências Principais                         |
| ----- | ---------------------------------- | ------- | --------------------------------------------- |
| RF-01 | Factura Electrónica (FE)           | 75%     | Lote, B2G, nominação >7M                      |
| RF-02 | Autofactura Electrónica (AFE)      | 60%     | RUC DNIT, bloqueio crédito IVA                |
| RF-03 | Nota de Crédito Electrónica (NCE)  | 50%     | Moeda/comprador, limite, motivos, estoque     |
| RF-04 | Nota de Débito Electrónica (NDE)   | 40%     | Moeda, custos                                 |
| RF-05 | Nota de Remisión Electrónica (NRE) | 40%     | Peso, motorista, veículo, Fleet               |
| RF-06 | Eventos SIFEN                      | 20%     | Transporte, conformidade, cancelamento prazos |
| RF-07 | Recibo Electrónico / Retención     | 0%      | Tudo                                          |
| RF-08 | Docs não-eletrônicos               | 10%     | Registro, classificação, Marangatú            |
| RF-09 | Multiempresa / Certificados        | 30%     | Certificado digital, alertas                  |
| RF-10 | Contabilidade / Reportes Fiscais   | 15%     | Libro IVA, Marangatú, dashboard               |
| RF-12 | Contingência Avançada              | 20%     | Detecção, cola, backoff                       |

---

## 2. Priorização

### MVP (Phase 1) — Crítico para operação

- RF-01.1: Nominação obrigatória por monto (>Gs. 7M)
- RF-03.1: Validação moeda/comprador vs factura original
- RF-03.2: Motivos de NCE
- RF-03.3: Limite de crédito (soma NCE ≤ original)
- RF-04.1: Validação moeda NDE
- RF-06.4: Cancelamento com prazos (48h FE/AFE, 168h NCE/NDE/NRE)
- RF-06.5: Cancelação com DTEs filhos

### Phase 2 — Operação completa

- RF-01.2: Emissão em lote (até 100 FE)
- RF-01.3: B2G — Campos contratação pública
- RF-01.4: Validação RUC activo SIFEN
- RF-02.1: Verificação RUC provedor via DNIT
- RF-02.2: Bloqueio crédito IVA em AFE
- RF-03.4: Reentrada de estoque (NCE devolução)
- RF-03.5: Asiento contable débito IVA
- RF-04.2: Documentação recuperação custos NDE
- RF-04.3: Validação tipo factura original NDE
- RF-05.1: Peso de mercadería obrigatório
- RF-05.2: Dados motorista e veículo
- RF-05.4: Aprovação SIFEN pre-despacho
- RF-06.1: Evento de transporte
- RF-06.2: Evento de conformidade/inconformidade
- RF-06.3: Evento de nominação
- RF-08.1: Registro faturas pre-impressas
- RF-08.2: Validação vigência timbrado
- RF-08.3: Classificação crédito IVA
- RF-09.1: Certificado digital por empresa
- RF-09.2: Alertas expiração certificado
- RF-10.1: Libro IVA Vendas
- RF-10.2: Libro IVA Compras
- RF-10.5: Dashboard status DTE
- RF-12.1: Detecção automática indisponibilidade
- RF-12.2: Cola de reenvio com prioridade
- RF-12.3: Reintento com backoff exponencial

### Phase 3 — Funcionalidades avançadas

- RF-05.3: Integração Fleet
- RF-07.1: Recibo Electrónico de Dinero
- RF-07.2: Comprobante de Retención
- RF-07.3: Compatibilidade Tesakã
- RF-08.4: Exportação Marangatú (RG 90/2021)
- RF-08.5: Outros docs não-eletrônicos
- RF-10.3: Exportação Marangatú
- RF-10.4: Consolidação multiempresa
- RF-10.6: Reporte de retenciones

---

## 3. Dependências Técnicas

| Dependência                         | RFs Afetados     | Tipo            |
| ----------------------------------- | ---------------- | --------------- |
| API DNIT (verificação RUC)          | RF-02.1          | External API    |
| Módulo Fleet                        | RF-05.3          | Odoo module     |
| Certificados PKCS#12 / cryptography | RF-09.1, RF-09.2 | Python lib      |
| Sistema Tesakã (DNIT)               | RF-07.3          | External system |
| Portal Marangatú                    | RF-08.4, RF-10.3 | Export format   |
| stock (Odoo)                        | RF-03.4          | Odoo module     |

---

## 4. Especificações BDD — Tarefas Pendentes

### Feature RF-01: Factura Electrónica — Pendências

```gherkin
# language: es
Funcionalidad: RF-01 Factura Electrónica - Funcionalidades Pendientes

  ## RF-01.1: Nominación obligatoria por monto

  Escenario: FE nominada obligatoria cuando monto supera Gs. 7.000.000
    Dado una factura electrónica con total de Gs. 8.000.000
    Y el cliente es "innominado" (sin RUC ni documento)
    Cuando intento confirmar la factura
    Entonces el sistema rechaza con "Monto superior a Gs. 7.000.000 requiere cliente nominado"

  Escenario: FE innominada permitida cuando monto no supera Gs. 7.000.000
    Dado una factura electrónica con total de Gs. 5.000.000
    Y el cliente es "innominado"
    Cuando confirmo la factura
    Entonces la factura se confirma exitosamente

  Escenario: FE innominada con monto exacto del límite
    Dado una factura electrónica con total de Gs. 7.000.000
    Y el cliente es "innominado"
    Cuando confirmo la factura
    Entonces la factura se confirma exitosamente

  ## RF-01.2: Emisión en lote

  Escenario: Emitir lote de hasta 100 FE simultáneamente
    Dado 100 facturas electrónicas en estado "to_send"
    Cuando ejecuto la acción "Enviar lote EDI"
    Entonces las 100 facturas se envían al proveedor en una sola transmisión
    Y cada factura recibe su CDC individual
    Y el tiempo total no supera 120 segundos

  Escenario: Lote excede límite de 100 documentos
    Dado 150 facturas electrónicas en estado "to_send"
    Cuando intento enviar como lote
    Entonces el sistema divide en 2 lotes (100 + 50)
    Y procesa secuencialmente

  ## RF-01.3: B2G - Campos de contratación pública

  Escenario: FE B2G con campos de contratación pública (Ley 7021/2022)
    Dado una factura electrónica para entidad gubernamental
    Y el campo "número de contrato público" es "CONT-2026-001"
    Y el campo "número de proceso licitatorio" es "LPN-2026-050"
    Cuando envío la factura al SIFEN
    Entonces el XML incluye los campos del grupo B2G
    Y la factura es aceptada

  Escenario: FE B2G sin campos obligatorios de contratación
    Dado una factura electrónica para entidad gubernamental
    Y los campos de contratación pública están vacíos
    Cuando intento enviar al SIFEN
    Entonces el sistema rechaza con "Campos de contratación pública obligatorios para B2G"

  ## RF-01.4: Validación RUC activo en SIFEN (B2B)

  Escenario: FE B2B con RUC receptor activo en SIFEN
    Dado una factura electrónica B2B
    Y el RUC del receptor "80012345-6" está activo en SIFEN
    Cuando envío la factura
    Entonces la validación de RUC pasa exitosamente
    Y la factura se transmite

  Escenario: FE B2B con RUC receptor inactivo en SIFEN
    Dado una factura electrónica B2B
    Y el RUC del receptor "80099999-1" está inactivo/suspendido en SIFEN
    Cuando intento enviar la factura
    Entonces el sistema muestra advertencia "RUC del receptor no está activo en SIFEN"
    Y permite forzar el envío con confirmación del usuario
```

### Feature RF-02: Autofactura Electrónica — Pendências

```gherkin
# language: es
Funcionalidad: RF-02 Autofactura Electrónica - Funcionalidades Pendientes

  ## RF-02.1: Verificación RUC proveedor via DNIT

  Escenario: AFE con verificación automática de RUC del proveedor
    Dado una autofactura electrónica para proveedor con RUC "80012345-6"
    Cuando creo la autofactura
    Entonces el sistema consulta el API DNIT para verificar estado del RUC
    Y muestra el resultado: "RUC Activo - Contribuyente"

  Escenario: AFE para proveedor sin RUC (microproductor)
    Dado una autofactura electrónica para proveedor sin RUC
    Y el proveedor tiene constancia de microproductor vigente
    Cuando creo la autofactura
    Entonces el sistema valida la constancia
    Y marca la autofactura como "sin crédito IVA"

  ## RF-02.2: Bloqueo crédito IVA

  Escenario: AFE no genera asiento de crédito IVA
    Dado una autofactura electrónica confirmada por Gs. 1.100.000 (IVA 10%)
    Cuando el sistema genera los asientos contables
    Entonces NO se genera asiento de crédito fiscal IVA
    Y el IVA se registra como gasto (cuenta de IVA no deducible)

  Escenario: AFE aparece en Libro IVA Compras sin crédito
    Dado una autofactura electrónica aceptada por SIFEN
    Cuando genero el Libro IVA de Compras
    Entonces la AFE aparece con columna "Crédito IVA" = 0
    Y la columna "IVA como Gasto" muestra el monto del IVA
```

### Feature RF-03: Nota de Crédito Electrónica — Pendências

```gherkin
# language: es
Funcionalidad: RF-03 Nota de Crédito Electrónica - Funcionalidades Pendientes

  ## RF-03.1: Validación moneda y comprador vs factura original

  Escenario: NCE con moneda diferente a factura original
    Dado una factura electrónica original en PYG
    Y creo una nota de crédito referenciando esa factura
    Y la nota de crédito está en USD
    Cuando intento confirmar la nota de crédito
    Entonces el sistema rechaza con "Moneda debe coincidir con factura original (PYG)"

  Escenario: NCE con comprador diferente a factura original
    Dado una factura electrónica original para "Comercial Guaraní SA" (RUC 80012345)
    Y creo una nota de crédito referenciando esa factura
    Pero el cliente de la NCE es "Consultora Paraná SRL" (RUC 80067890)
    Cuando intento confirmar la nota de crédito
    Entonces el sistema rechaza con "Cliente debe coincidir con factura original"

  ## RF-03.2: Motivos de NCE

  Escenario: NCE con motivo "Devolución"
    Dado una nota de crédito electrónica
    Y selecciono el motivo "Devolución"
    Cuando confirmo la nota de crédito
    Entonces el campo motivo se incluye en el XML SIFEN
    Y se activa la reentrada de productos en inventario

  Esquema del escenario: NCE con motivos válidos
    Dado una nota de crédito electrónica
    Y selecciono el motivo "<motivo>"
    Cuando confirmo la nota de crédito
    Entonces la nota de crédito es válida

    Ejemplos:
      | motivo              |
      | Devolución          |
      | Descuento           |
      | Bonificación        |
      | Crédito Incobrable  |

  Escenario: NCE sin motivo
    Dado una nota de crédito electrónica sin motivo seleccionado
    Cuando intento confirmar
    Entonces el sistema rechaza con "Motivo obligatorio para Nota de Crédito"

  ## RF-03.3: Límite de crédito (suma NCE ≤ original)

  Escenario: NCE parcial dentro del límite
    Dado una factura electrónica original por Gs. 1.100.000 (IVA total Gs. 100.000)
    Y ya existe una NCE parcial por Gs. 550.000
    Cuando creo otra NCE parcial por Gs. 550.000
    Entonces la NCE es válida (suma = Gs. 1.100.000 = total original)

  Escenario: NCE excede total de factura original
    Dado una factura electrónica original por Gs. 1.100.000
    Y ya existe una NCE parcial por Gs. 800.000
    Cuando creo otra NCE por Gs. 500.000
    Entonces el sistema rechaza con "Suma de NCE (Gs. 1.300.000) excede total de factura original (Gs. 1.100.000)"

  Escenario: NCE para factura cancelada
    Dado una factura electrónica que fue cancelada en SIFEN
    Cuando intento crear una NCE referenciando esa factura
    Entonces el sistema rechaza con "No se puede emitir NCE para factura cancelada"

  ## RF-03.4: Reentrada de estoque

  Escenario: NCE por devolución reingresa productos al inventario
    Dado una factura electrónica con 5 unidades de "Notebook Dell Inspiron"
    Y creo una NCE por devolución de 3 unidades
    Cuando confirmo la nota de crédito
    Entonces se crea un movimiento de stock de entrada por 3 unidades
    Y el stock disponible aumenta en 3 unidades

  ## RF-03.5: Asiento contable débito IVA

  Escenario: NCE genera asiento de débito IVA automático
    Dado una nota de crédito electrónica por Gs. 1.100.000 (IVA 10%)
    Cuando confirmo la nota de crédito
    Entonces se genera un asiento contable de débito IVA por Gs. 100.000
    Y la cuenta de IVA Débito Fiscal se debita
```

### Feature RF-04: Nota de Débito Electrónica — Pendências

```gherkin
# language: es
Funcionalidad: RF-04 Nota de Débito Electrónica - Funcionalidades Pendientes

  ## RF-04.1: Validación moneda

  Escenario: NDE con moneda diferente a factura original
    Dado una factura electrónica original en PYG
    Y creo una nota de débito referenciando esa factura
    Y la nota de débito está en USD
    Cuando intento confirmar
    Entonces el sistema rechaza con "Moneda debe coincidir con factura original"

  ## RF-04.2: Documentación de recuperación de costos

  Escenario: NDE con categoría de costo/gasto
    Dado una nota de débito electrónica
    Y selecciono la categoría "Flete adicional"
    Y adjunto el comprobante de gasto
    Cuando confirmo la nota de débito
    Entonces la NDE incluye la documentación de respaldo en el XML

  Escenario: NDE sin documentación de costos
    Dado una nota de débito electrónica sin categoría de costo
    Cuando intento confirmar
    Entonces el sistema muestra advertencia "Se recomienda documentar el motivo del débito"

  ## RF-04.3: Validación tipo factura original

  Escenario: NDE solo puede referenciar factura (no NCE ni NRE)
    Dado una nota de débito electrónica
    Y el documento asociado referencia una NCE (código 5)
    Cuando intento confirmar
    Entonces el sistema rechaza con "NDE solo puede referenciar Facturas (código 1)"
```

### Feature RF-05: Nota de Remisión Electrónica — Pendências

```gherkin
# language: es
Funcionalidad: RF-05 Nota de Remisión Electrónica - Funcionalidades Pendientes

  ## RF-05.1: Peso de mercadería obligatorio

  Escenario: NRE con peso de mercadería
    Dado una nota de remisión electrónica
    Y el peso total es 500 kg
    Y la unidad de peso es "kg"
    Cuando confirmo la nota de remisión
    Entonces el campo peso se incluye en el XML SIFEN (E927)

  Escenario: NRE sin peso de mercadería
    Dado una nota de remisión electrónica de mercadería física
    Y el campo peso está vacío
    Cuando intento confirmar
    Entonces el sistema rechaza con "Peso de mercadería obligatorio para NRE"

  Esquema del escenario: NRE con diferentes unidades de peso
    Dado una nota de remisión con peso <peso> <unidad>
    Cuando confirmo la nota de remisión
    Entonces el peso se registra correctamente

    Ejemplos:
      | peso  | unidad |
      | 500   | kg     |
      | 35    | arroba |
      | 2.5   | ton    |

  ## RF-05.2: Datos de motorista y vehículo

  Escenario: NRE con datos de conductor
    Dado una nota de remisión electrónica
    Y el conductor es "Juan Pérez" con CI "4567890"
    Y la licencia de conducir es "C-12345678"
    Cuando confirmo la nota de remisión
    Entonces los datos del conductor se incluyen en el XML (E960-E969)

  Escenario: NRE con datos de vehículo
    Dado una nota de remisión electrónica
    Y el vehículo tiene placa "ABC-1234"
    Y el tipo de vehículo es "Camión"
    Y la marca es "Mercedes-Benz"
    Cuando confirmo la nota de remisión
    Entonces los datos del vehículo se incluyen en el XML (E970-E979)

  Escenario: NRE sin datos de transporte
    Dado una nota de remisión electrónica
    Y los campos de conductor y vehículo están vacíos
    Cuando intento confirmar
    Entonces el sistema rechaza con "Datos de conductor y vehículo obligatorios para NRE"

  ## RF-05.3: Integración con módulo Fleet (Phase 3)

  Escenario: NRE con datos pre-llenados desde Fleet
    Dado un vehículo registrado en Fleet con placa "ABC-1234"
    Y un conductor asignado "Juan Pérez"
    Cuando creo una nota de remisión y selecciono el vehículo de Fleet
    Entonces los campos de conductor, licencia, placa y tipo se llenan automáticamente

  ## RF-05.4: Aprobación SIFEN pre-despacho

  Escenario: NRE requiere aprobación SIFEN antes del despacho
    Dado una nota de remisión electrónica lista para enviar
    Cuando envío la NRE al SIFEN
    Y el SIFEN la acepta con CDC
    Entonces el estado cambia a "Aprobada para despacho"
    Y se habilita el botón "Imprimir KuDE para conductor"

  Escenario: NRE rechazada por SIFEN bloquea despacho
    Dado una nota de remisión electrónica enviada al SIFEN
    Y el SIFEN la rechaza
    Entonces el estado cambia a "Rechazada"
    Y se muestra alerta "No se puede despachar mercadería sin aprobación SIFEN"
```

### Feature RF-06: Eventos SIFEN — Pendências

```gherkin
# language: es
Funcionalidad: RF-06 Eventos SIFEN - Funcionalidades Pendientes

  ## RF-06.1: Evento de Transporte

  Escenario: Registrar cambio de conductor en NRE activa
    Dado una nota de remisión electrónica aceptada por SIFEN
    Y el conductor original es "Juan Pérez"
    Cuando registro un evento de transporte "Cambio de conductor"
    Y el nuevo conductor es "Carlos López" con CI "5678901"
    Entonces el evento se envía al SIFEN en menos de 30 segundos
    Y el SIFEN confirma el evento con código de respuesta

  Escenario: Registrar cambio de ruta
    Dado una nota de remisión electrónica aceptada
    Y la ruta original es "Asunción → Ciudad del Este"
    Cuando registro un evento de transporte "Cambio de ruta"
    Y la nueva ruta es "Asunción → Encarnación → Ciudad del Este"
    Entonces el evento se registra y envía al SIFEN

  Escenario: Registrar cambio de vehículo
    Dado una nota de remisión electrónica aceptada
    Cuando registro un evento de transporte "Cambio de vehículo"
    Y el nuevo vehículo tiene placa "XYZ-5678"
    Entonces el evento se envía al SIFEN
    Y se actualiza la información del vehículo en la NRE

  ## RF-06.2: Evento de Conformidad/Inconformidad

  Escenario: Receptor marca conformidad de DTE recibido
    Dado una factura electrónica recibida con CDC "01800123456001001000000012025010112345678901"
    Cuando el receptor marca "Conforme"
    Y añade observación "Mercadería recibida completa"
    Entonces se envía evento de conformidad al SIFEN
    Y el estado del DTE cambia a "Conforme"
    Y se dispara la conciliación contable automática

  Escenario: Receptor marca inconformidad
    Dado una factura electrónica recibida
    Cuando el receptor marca "No conforme"
    Y selecciona motivo "Mercadería incompleta"
    Y detalla "Faltaron 5 unidades del ítem 2"
    Entonces se envía evento de inconformidad al SIFEN
    Y el estado del DTE cambia a "No conforme"
    Y se crea una alerta para el emisor

  ## RF-06.3: Evento de Nominación

  Escenario: Nominar documento complementario a FE
    Dado una factura electrónica aceptada
    Cuando registro un evento de nominación
    Y vinculo un permiso de exportación "EXP-2026-001"
    Entonces el evento de nominación se envía al SIFEN
    Y el documento complementario queda asociado

  ## RF-06.4: Cancelamiento con límites de tiempo

  Escenario: Cancelar FE dentro de 48 horas
    Dado una factura electrónica aceptada hace 24 horas
    Cuando solicito la cancelación con motivo "Error en datos del receptor"
    Entonces la cancelación se envía al SIFEN
    Y el estado cambia a "Cancelado"

  Escenario: Cancelar FE después de 48 horas
    Dado una factura electrónica aceptada hace 72 horas
    Cuando intento cancelar la factura
    Entonces el sistema rechaza con "Plazo de cancelación excedido (48h para FE/AFE)"
    Y sugiere "Emita una Nota de Crédito en su lugar"

  Escenario: Cancelar NCE dentro de 168 horas
    Dado una nota de crédito electrónica aceptada hace 120 horas
    Cuando solicito la cancelación
    Entonces la cancelación se envía al SIFEN exitosamente

  Escenario: Cancelar NCE después de 168 horas
    Dado una nota de crédito electrónica aceptada hace 200 horas
    Cuando intento cancelar
    Entonces el sistema rechaza con "Plazo de cancelación excedido (168h para NCE/NDE/NRE)"

  Esquema del escenario: Límites de cancelación por tipo de documento
    Dado un DTE tipo "<tipo>" aceptado hace <horas> horas
    Cuando intento cancelar
    Entonces el resultado es "<resultado>"

    Ejemplos:
      | tipo | horas | resultado                          |
      | FE   | 24    | Cancelado exitosamente             |
      | FE   | 49    | Plazo excedido (48h)               |
      | AFE  | 47    | Cancelado exitosamente             |
      | AFE  | 50    | Plazo excedido (48h)               |
      | NCE  | 100   | Cancelado exitosamente             |
      | NCE  | 169   | Plazo excedido (168h)              |
      | NDE  | 167   | Cancelado exitosamente             |
      | NDE  | 170   | Plazo excedido (168h)              |
      | NRE  | 168   | Cancelado exitosamente             |
      | NRE  | 200   | Plazo excedido (168h)              |

  ## RF-06.5: Cancelación con DTEs hijos

  Escenario: Cancelar FE que tiene NCE activa
    Dado una factura electrónica con una NCE activa referenciándola
    Cuando intento cancelar la factura
    Entonces el sistema rechaza con "Cancele primero las NCE/NDE asociadas antes de cancelar la FE"

  Escenario: Cancelar FE después de cancelar NCE hija
    Dado una factura electrónica con una NCE que fue cancelada
    Cuando intento cancelar la factura
    Entonces la cancelación se procesa exitosamente
```

### Feature RF-07: Recibo Electrónico e Retención — Pendências

```gherkin
# language: es
Funcionalidad: RF-07 Recibo Electrónico y Comprobante de Retención

  ## RF-07.1: Recibo Electrónico de Dinero

  Escenario: Emitir recibo electrónico por pago de cuota
    Dado una factura electrónica a crédito con 3 cuotas de Gs. 366.667
    Y el cliente paga la primera cuota
    Cuando emito el recibo electrónico
    Entonces el recibo vincula al CDC de la factura original
    Y el monto del recibo es Gs. 366.667
    Y la factura se marca como "Pago parcial (1/3)"

  Escenario: Recibo electrónico marca factura como pagada
    Dado una factura electrónica a crédito con saldo pendiente Gs. 366.667
    Y el cliente paga el saldo total
    Cuando emito el recibo electrónico
    Entonces la factura se marca como "Pagada"
    Y se reconcilia automáticamente con el asiento de pago

  ## RF-07.2: Comprobante de Retención (Phase 3)

  Escenario: Emitir comprobante de retención IVA
    Dado una factura de compra por Gs. 11.000.000 (IVA 10%)
    Y la empresa es agente de retención IVA
    Cuando registro el pago con retención
    Entonces se calcula retención IVA = Gs. 1.000.000 × 30% = Gs. 300.000
    Y se emite comprobante de retención via SIFEN
    Y se paga al proveedor Gs. 10.700.000

  Escenario: Emitir comprobante de retención IRE
    Dado una factura de compra de servicios por Gs. 5.000.000
    Y la empresa es agente de retención IRE
    Cuando registro el pago con retención
    Entonces se calcula retención IRE según código tributario
    Y se emite el comprobante correspondiente

  ## RF-07.3: Compatibilidad Tesakã

  Escenario: Generar retención virtual via Tesakã
    Dado que la empresa usa el sistema Tesakã para retenciones virtuales
    Cuando genero una retención
    Entonces el formato de salida es compatible con plantilla DNIT Tesakã
    Y se puede cargar directamente en el portal Tesakã
```

### Feature RF-08: Documentos Não-Eletrônicos — Pendências

```gherkin
# language: es
Funcionalidad: RF-08 Documentos No Electrónicos

  ## RF-08.1: Registro de facturas pre-impresas recibidas

  Escenario: Registrar factura pre-impresa de proveedor
    Dado que recibo una factura pre-impresa del proveedor "Distribuidora del Este SA"
    Y el timbrado es "12345678"
    Y el número es "001-001-0000456"
    Y la fecha de emisión es "2026-01-15"
    Cuando registro la factura en el sistema
    Entonces se valida el formato del timbrado (8 dígitos)
    Y se valida el formato de numeración (XXX-XXX-NNNNNNN)
    Y se registra como factura de compra

  Escenario: Registrar factura pre-impresa con timbrado inválido
    Dado que intento registrar una factura pre-impresa
    Y el timbrado es "1234" (menos de 8 dígitos)
    Cuando intento guardar
    Entonces el sistema rechaza con "Formato de timbrado inválido (debe ser 8 dígitos)"

  ## RF-08.2: Validación de vigencia del timbrado recibido

  Escenario: Factura pre-impresa con timbrado vigente
    Dado una factura pre-impresa con timbrado vigente hasta "2026-12-31"
    Y la fecha de emisión es "2026-03-15"
    Cuando registro la factura
    Entonces la validación de vigencia pasa exitosamente

  Escenario: Factura pre-impresa con timbrado vencido
    Dado una factura pre-impresa con timbrado vigente hasta "2025-12-31"
    Y la fecha de emisión es "2026-01-15"
    Cuando intento registrar
    Entonces el sistema muestra advertencia "Timbrado vencido al momento de emisión"
    Y permite registrar con confirmación del usuario

  ## RF-08.3: Clasificación automática crédito IVA

  Escenario: Factura de proveedor contribuyente genera crédito IVA
    Dado una factura pre-impresa de proveedor con RUC activo
    Y el proveedor es contribuyente (tipo 1)
    Cuando registro la factura
    Entonces se clasifica como "Con crédito IVA"
    Y el IVA se registra en cuenta de Crédito Fiscal

  Escenario: Factura de proveedor sin RUC no genera crédito IVA
    Dado una factura pre-impresa de proveedor sin RUC
    Y el proveedor es no contribuyente (tipo 2)
    Cuando registro la factura
    Entonces se clasifica como "Sin crédito IVA"
    Y el IVA se registra como gasto

  ## RF-08.4: Exportación formato Marangatú (RG 90/2021)

  Escenario: Exportar registro de comprobantes para Marangatú
    Dado 50 facturas pre-impresas registradas en el período enero 2026
    Cuando exporto en formato Marangatú
    Entonces se genera un archivo CSV con codificación UTF-8
    Y las columnas son: Timestamp, Tipo, Timbrado, Emisor, Base Imponible, IVA 5%, IVA 10%, Exento, Total
    Y el formato de fecha es "YYYY-MM-DD HH:MM:SS"
    Y los montos tienen 2 decimales

  ## RF-08.5: Otros documentos no electrónicos

  Escenario: Registrar boleta de venta
    Dado una boleta de venta del régimen simplificado
    Cuando registro en el sistema
    Entonces se clasifica como "Sin crédito IVA" automáticamente

  Escenario: Registrar ticket de caja registradora
    Dado un ticket de caja registradora
    Cuando registro en el sistema
    Entonces se registra como gasto sin crédito fiscal
```

### Feature RF-09: Multiempresa e Certificados — Pendências

```gherkin
# language: es
Funcionalidad: RF-09 Multiempresa y Certificados Digitales

  ## RF-09.1: Certificado digital por empresa

  Escenario: Configurar certificado digital PKCS#12 por empresa
    Dado la empresa "Comercial ABC SA" con RUC "80012345-6"
    Cuando cargo un certificado digital en formato .pfx
    Y ingreso la contraseña del certificado
    Entonces el certificado se almacena encriptado (AES-256)
    Y se asocia exclusivamente a la empresa
    Y se muestra la fecha de expiración del certificado

  Escenario: Certificado no puede compartirse entre empresas
    Dado un certificado digital asociado a empresa "Comercial ABC SA"
    Cuando intento asignar el mismo certificado a "Distribuidora XYZ SRL"
    Entonces el sistema rechaza con "Cada empresa debe tener certificado propio (un RUC por certificado)"

  ## RF-09.2: Alertas de expiración de certificado

  Escenario: Alerta 60 días antes de expiración
    Dado un certificado digital que expira en 55 días
    Cuando un usuario de la empresa inicia sesión
    Entonces se muestra banner de advertencia "Certificado digital expira en 55 días"

  Escenario: Alerta 30 días antes de expiración
    Dado un certificado digital que expira en 28 días
    Cuando un usuario accede al módulo de facturación
    Entonces se muestra alerta urgente "Certificado digital expira en 28 días - Renueve inmediatamente"
    Y se envía email al administrador

  Escenario: Alerta 7 días antes de expiración
    Dado un certificado digital que expira en 5 días
    Cuando un usuario intenta emitir una factura
    Entonces se muestra alerta crítica "Certificado expira en 5 días - La emisión puede detenerse"
    Y se envía notificación diaria al administrador

  Escenario: Certificado expirado bloquea emisión
    Dado un certificado digital expirado
    Cuando intento enviar una factura al SIFEN
    Entonces el sistema bloquea con "Certificado digital expirado - No se puede firmar el documento"
```

### Feature RF-10: Contabilidade e Reportes Fiscais — Pendências

```gherkin
# language: es
Funcionalidad: RF-10 Contabilidad y Reportes Fiscales

  ## RF-10.1: Libro IVA Ventas

  Escenario: Generar Libro IVA Ventas del período
    Dado 100 facturas electrónicas emitidas en enero 2026
    Y 15 notas de crédito emitidas en enero 2026
    Cuando genero el Libro IVA Ventas para enero 2026
    Entonces el reporte incluye todas las FE y NCE del período
    Y las columnas son: Fecha, Tipo DTE, CDC/Timbrado, Receptor (RUC/Nombre), Base Imponible, IVA 5%, IVA 10%, Exento, Total
    Y los totales al pie cuadran con la suma de cada columna
    Y las NCE aparecen con montos negativos
    Y el tiempo de generación es menor a 10 segundos

  Escenario: Libro IVA Ventas con filtro por tipo DTE
    Dado facturas electrónicas y notas de crédito en el período
    Cuando genero el Libro IVA Ventas filtrado por "Solo Facturas"
    Entonces solo aparecen las FE (código 1) en el reporte

  ## RF-10.2: Libro IVA Compras

  Escenario: Generar Libro IVA Compras del período
    Dado 80 facturas de compra registradas en enero 2026
    Incluyendo facturas electrónicas recibidas y pre-impresas
    Cuando genero el Libro IVA Compras para enero 2026
    Entonces el reporte incluye ambos tipos de facturas
    Y distingue entre "Con crédito IVA" y "Sin crédito IVA"
    Y los totales de crédito fiscal cuadran

  ## RF-10.3: Exportación Marangatú

  Escenario: Exportar Libro IVA en formato Marangatú (RG 90/2021)
    Dado el Libro IVA Ventas de enero 2026 generado
    Cuando exporto en formato Marangatú
    Entonces se genera archivo CSV con codificación UTF-8
    Y el formato cumple con las especificaciones de RG 90/2021
    Y el archivo puede importarse directamente en el portal Marangatú

  ## RF-10.4: Consolidación multiempresa

  Escenario: Libro IVA consolidado de múltiples empresas
    Dado 3 empresas paraguayas con facturas en enero 2026
    Cuando genero el Libro IVA Consolidado
    Entonces muestra subtotales por empresa
    Y un gran total consolidado
    Y cada empresa se identifica por su RUC

  ## RF-10.5: Dashboard de status DTE

  Escenario: Visualizar dashboard de estado de DTEs
    Dado 500 DTEs emitidos en el mes actual
    Cuando accedo al dashboard de Facturación Electrónica
    Entonces veo:
      | Estado     | Cantidad | Porcentaje |
      | Aceptados  | 450      | 90%        |
      | Rechazados | 10       | 2%         |
      | Pendientes | 30       | 6%         |
      | Error      | 5        | 1%         |
      | Cancelados | 5        | 1%         |
    Y puedo filtrar por tipo de DTE, período, y proveedor EDI
    Y puedo hacer clic en cada estado para ver los documentos

  Escenario: Dashboard muestra alertas de plazo de transmisión
    Dado 5 DTEs con plazo de transmisión venciendo en menos de 12 horas
    Cuando accedo al dashboard
    Entonces veo alerta "5 documentos con plazo de transmisión próximo a vencer"
    Y puedo enviarlos en lote desde el dashboard

  ## RF-10.6: Reporte de retenciones (Phase 3)

  Escenario: Generar reporte de retenciones realizadas
    Dado retenciones IVA e IRE realizadas en el período
    Cuando genero el reporte de retenciones
    Entonces agrupa por tipo (IVA/IRE) y por proveedor
    Y muestra totales por tipo de retención
    Y puede exportarse para declaración jurada
```

### Feature RF-12: Contingência Avançada — Pendências

```gherkin
# language: es
Funcionalidad: RF-12 Contingencia Avanzada

  ## RF-12.1: Detección automática de indisponibilidad SIFEN

  Escenario: SIFEN indisponible por más de 30 minutos
    Dado que los últimos 3 intentos de envío al SIFEN fallaron
    Y el tiempo desde el primer fallo supera 30 minutos
    Cuando intento enviar una nueva factura
    Entonces el sistema activa modo contingencia automáticamente
    Y muestra alerta "SIFEN indisponible - Modo contingencia activado"
    Y los documentos se generan localmente con emission_type="2"

  ## RF-12.2: Cola de reenvío con prioridad

  Escenario: Reenvío prioriza documentos por deadline
    Dado 10 documentos en cola de contingencia
    Y 3 de ellos tienen deadline en menos de 6 horas
    Cuando el SIFEN vuelve a estar disponible
    Y se ejecuta el cron de reenvío
    Entonces los 3 documentos urgentes se envían primero
    Y luego se procesan los restantes por orden cronológico

  ## RF-12.3: Reintento con backoff exponencial

  Escenario: Reintento automático con backoff
    Dado un documento rechazado por error de comunicación
    Cuando el cron de reenvío lo procesa
    Entonces el primer reintento es después de 1 minuto
    Y el segundo reintento después de 5 minutos
    Y el tercero después de 15 minutos
    Y el cuarto después de 60 minutos
    Y el quinto (máximo) después de 120 minutos
    Y después de 5 intentos, se marca como "Error - Intervención manual requerida"
```
