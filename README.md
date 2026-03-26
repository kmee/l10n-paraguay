# Localización Paraguay para Odoo

Repositorio de módulos para la **localización paraguaya** de Odoo 16.0,
desarrollado siguiendo las convenciones de la
[Odoo Community Association (OCA)](https://odoo-community.org/).

## Descripción General

Este repositorio implementa la localización fiscal y contable de Paraguay,
cubriendo desde el Plan de Cuentas oficial hasta la **Facturación Electrónica
(SIFEN)** y el **Régimen de Maquila** (Ley 1064/97), según las normativas de
la SET (Subsecretaría de Estado de Tributación), el Decreto 7.795/2017 y la
legislación de maquila vigente.

### Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                    Régimen de Maquila                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ maquila_ops  │ │ maquila_mrp  │ │ maquila_report           │ │
│  │ Admisión,    │ │ BOM+INTN,    │ │ CNIME, Dashboard,        │ │
│  │ Exportación, │ │ VAN, Waste   │ │ SIFEN ext, SIMEX         │ │
│  │ Garantías,   │ └──────┬───────┘ └────────────┬─────────────┘ │
│  │ TUM, IVA     │        │                      │               │
│  └──────┬───────┘        │                      │               │
│         └────────┬───────┘                      │               │
│                  ▼                              │               │
│         ┌──────────────────┐                    │               │
│         │ maquila_base     │◄───────────────────┘               │
│         │ Programa, CNIME, │                                    │
│         │ Contratos, INTN  │                                    │
│         └────────┬─────────┘                                    │
├──────────────────┼──────────────────────────────────────────────┤
│                  ▼                                              │
│              Conectores EDI (Proveedores)                        │
│  ┌─────────────┐ ┌───────────────┐ ┌──────────────────────────┐│
│  │ edi_factpy  │ │edi_facturasend│ │ edi_sifen (directo)      ││
│  └──────┬──────┘ └───────┬───────┘ └────────────┬─────────────┘│
│         └────────┬───────┘                      │              │
│                  ▼                              │              │
│         ┌───────────────────────┐               │              │
│         │  l10n_py_edi_base     │◄──────────────┘              │
│         │  CDC, KuDE, Grupo H,  │                              │
│         │  Validaciones, DTE    │                              │
│         └───────────┬───────────┘                              │
│                     ▼                                          │
│         ┌───────────────────────┐                              │
│         │  l10n_py_account      │  ← Contabilidad              │
│         │  Timbrado, Numeración,│                              │
│         │  IVA SIFEN, Demo      │                              │
│         └─────┬─────────┬───────┘                              │
│               ▼         ▼                                      │
│  ┌──────────────────┐  ┌─────────────────┐                    │
│  │  l10n_py_base    │  │  l10n_py        │                    │
│  │  RUC, Geografía, │  │  Plan de Cuentas│                    │
│  │  Partner, Ciudad │  │  Impuestos PY   │                    │
│  └──────────────────┘  └─────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

## Módulos Disponibles

### Localización Base y EDI

| Módulo | Versión | Licencia | Descripción |
|--------|---------|----------|-------------|
| [l10n_py](l10n_py/) | 16.0.1.1.0 | LGPL-3 | Plan de Cuentas Paraguay (RG 49/14) — 222 cuentas, 6 impuestos |
| [l10n_py_base](l10n_py_base/) | 16.0.1.2.0 | LGPL-3 | Datos base: departamentos, ciudades, barrios, validación RUC |
| [l10n_py_account](l10n_py_account/) | 16.0.2.0.0 | LGPL-3 | Timbrado (autorización SET), numeración, fórmulas IVA SIFEN |
| [l10n_py_edi_base](l10n_py_edi_base/) | 16.0.3.0.0 | LGPL-3 | Core EDI: CDC, KuDE, documentos asociados, ciclo de vida DTE |
| [l10n_py_edi_sifen](l10n_py_edi_sifen/) | 16.0.2.0.0 | LGPL-3 | Conector EDI directo SIFEN via pysifen |
| [l10n_py_edi_factpy](l10n_py_edi_factpy/) | 16.0.1.2.0 | LGPL-3 | Conector EDI para proveedor FactPy |
| [l10n_py_edi_facturasend](l10n_py_edi_facturasend/) | 16.0.1.2.0 | LGPL-3 | Conector EDI para proveedor FacturaSend |

### Régimen de Maquila (Ley 1064/97)

| Módulo | Versión | Licencia | Descripción |
|--------|---------|----------|-------------|
| [l10n_py_maquila_base](l10n_py_maquila_base/) | 16.0.1.0.0 | AGPL-3 | Programa maquila, contratos CNIME, certificados INTN, alertas |
| [l10n_py_maquila_ops](l10n_py_maquila_ops/) | 16.0.1.0.0 | AGPL-3 | Admisión temporaria, exportación, garantías, TUM 1%, IVA, remesas |
| [l10n_py_maquila_mrp](l10n_py_maquila_mrp/) | 16.0.1.0.0 | AGPL-3 | BOM con coeficientes INTN, VAN, contenido regional, residuos |
| [l10n_py_maquila_report](l10n_py_maquila_report/) | 16.0.1.0.0 | AGPL-3 | Informe CNIME, dashboard, extensión SIFEN, SIMEX stubs |

## Tipos de Documento Electrónico Soportados

| Código | Tipo | Estado |
|--------|------|--------|
| 1 | Factura Electrónica (FE) | Implementado |
| 4 | Autofactura Electrónica (AFE) | Implementado |
| 5 | Nota de Crédito Electrónica (NCE) | Implementado |
| 6 | Nota de Débito Electrónica (NDE) | Implementado |
| 7 | Nota de Remisión Electrónica (NRE) | Implementado |

## Instalación

### Dependencias Python

```
num2words
qrcode
requests
cryptography
pykude
sifen
```

### Instalación de módulos

```bash
# Localización base + facturación electrónica
odoo-bin -d mi_base -i l10n_py,l10n_py_base,l10n_py_account,l10n_py_edi_base --stop-after-init

# Conector EDI (elegir uno)
odoo-bin -d mi_base -i l10n_py_edi_sifen --stop-after-init
# o
odoo-bin -d mi_base -i l10n_py_edi_factpy --stop-after-init

# Régimen de Maquila (requiere módulos OCA: agreement, contract,
# stock_analytic, mrp_bom_line_net_qty, mrp_account_analytic)
odoo-bin -d mi_base -i l10n_py_maquila_base,l10n_py_maquila_ops,l10n_py_maquila_mrp,l10n_py_maquila_report --stop-after-init
```

### Con Doodba (Docker)

```bash
# Localización + EDI
invoke install -m l10n_py,l10n_py_base,l10n_py_account,l10n_py_edi_base

# Maquila
invoke install -m l10n_py_maquila_base,l10n_py_maquila_ops,l10n_py_maquila_mrp,l10n_py_maquila_report

# Tests
invoke test -m l10n_py_account,l10n_py_edi_base
```

## Normativas Implementadas

### Tributación y Facturación Electrónica
- **RG 49/14** — Plan de Cuentas oficial del Ministerio de Hacienda
- **Decreto 7.795/2017** — Sistema Integrado de Facturación Electrónica Nacional (SIFEN)
- **MT SIFEN v150** — Manual Técnico del SIFEN versión 150
- **Ley 6.380/2019** — Modernización y simplificación del sistema tributario

### Régimen de Maquila
- **Ley 1.064/97** — Régimen de Maquila de Exportación
- **Decreto 9.585/2000** — Reglamentación de la Ley de Maquila
- **Resoluciones CNIME** — Contratos y programas de maquila
- **TUM 1%** — Tributo Único de Maquila sobre el Valor Agregado Nacional

## Roadmap

### EDI / SIFEN
Consulte [PRD_TAREFAS_PENDENTES.md](PRD_TAREFAS_PENDENTES.md) para el detalle
completo de funcionalidades EDI pendientes con especificaciones BDD (Gherkin):

- Emisión en lote, B2G, nominación obligatoria (RF-01)
- Eventos SIFEN: transporte, conformidad, cancelación con plazos (RF-06)
- Recibo electrónico y comprobantes de retención (RF-07)
- Libro IVA Ventas/Compras, exportación Marangatú, dashboard (RF-10)
- Contingencia avanzada con backoff exponencial (RF-12)

### Maquila
Funcionalidades pendientes del régimen de maquila:

- Integración Purchase/Sale con auto-asignación de posición fiscal
- Cálculo real de `qty_consumed`/`qty_remaining` en admisiones
- Tests unitarios para todos los módulos
- Integración SIMEX online (actualmente genera payload offline)

## Contribución

Este proyecto sigue las
[directrices de contribución de la OCA](https://github.com/OCA/odoo-community.org/blob/master/website/Ede/Contribute/CONTRIBUTING.rst).

Para contribuir:

1. Fork del repositorio
2. Crear branch desde `16.0`
3. Implementar cambios con tests
4. Ejecutar `pre-commit run -a`
5. Abrir Pull Request

## Créditos

### Autores

- [KMEE](https://kmee.com.br)

### Mantenedores

Este repositorio es mantenido por la OCA.

[![Odoo Community Association](https://odoo-community.org/logo.png)](https://odoo-community.org)

## Licencia

Módulos base: [LGPL-3](LICENSE)
Módulos maquila: [AGPL-3](https://www.gnu.org/licenses/agpl-3.0.html)
(por dependencia en módulos OCA AGPL-3)
