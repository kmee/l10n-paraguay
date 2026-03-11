[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# Odoo Paraguay Localization

[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/l10n-paraguay&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/l10n-paraguay/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/l10n-paraguay/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/l10n-paraguay/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/l10n-paraguay/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/l10n-paraguay/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/l10n-paraguay)

# Localización Paraguay para Odoo

Repositorio de módulos para la **localización paraguaya** de Odoo 16.0,
desarrollado siguiendo las convenciones de la
[Odoo Community Association (OCA)](https://odoo-community.org/).

## Descripción General

Este repositorio implementa la localización fiscal y contable de Paraguay,
cubriendo desde el Plan de Cuentas oficial hasta la **Facturación Electrónica
(SIFEN)** según las normativas de la SET (Subsecretaría de Estado de Tributación)
y el Decreto 7.795/2017 con sus actualizaciones.

### Arquitectura

Los módulos están organizados en capas con dependencias claras:

```
┌─────────────────────────────────────────────────────┐
│              Conectores EDI (Proveedores)            │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │ l10n_py_edi_     │  │ l10n_py_edi_             │ │
│  │ factpy           │  │ facturasend              │ │
│  └────────┬─────────┘  └────────────┬─────────────┘ │
│           │                         │               │
│           └───────────┬─────────────┘               │
│                       ▼                             │
│           ┌───────────────────────┐                 │
│           │  l10n_py_edi_base     │  ← Core EDI     │
│           │  CDC, KuDE, Grupo H,  │                 │
│           │  Validações, Lifecycle │                 │
│           └───────────┬───────────┘                 │
│                       ▼                             │
│           ┌───────────────────────┐                 │
│           │  l10n_py_account      │  ← Contabilidad │
│           │  Timbrado, Numeração, │                 │
│           │  IVA SIFEN, Demo Data │                 │
│           └─────┬─────────┬───────┘                 │
│                 ▼         ▼                         │
│  ┌──────────────────┐  ┌─────────────────┐         │
│  │  l10n_py_base    │  │  l10n_py        │         │
│  │  RUC, Geografía, │  │  Plan de Cuentas│         │
│  │  Partner, Ciudad │  │  Impuestos PY   │         │
│  └──────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────┘
```

**Capa Base** — `l10n_py` y `l10n_py_base` proporcionan el Plan de Cuentas
(RG 49/14), impuestos (IVA 10%, 5%, Exento), datos geográficos (departamentos,
ciudades, barrios) y extensiones del partner (RUC, tipo de contribuyente).

**Capa Contable** — `l10n_py_account` agrega el sistema de timbrado
(autorización SET), numeración secuencial (XXX-XXX-NNNNNNN), cálculo IVA
según fórmulas SIFEN v150 (campos F003-F023), y datos demo completos.

**Capa EDI** — `l10n_py_edi_base` implementa el ciclo de vida completo de
Documentos Tributarios Electrónicos (DTE): generación de CDC (44 dígitos),
código de seguridad, QR, KuDE (PDF), documentos asociados (Grupo H),
inutilización de números, y validación por tipo de documento (FE, AFE, NCE,
NDE, NRE).

**Conectores** — `l10n_py_edi_factpy` y `l10n_py_edi_facturasend` conectan
con proveedores de servicios EDI homologados por la SET, abstrayendo la
comunicación con el SIFEN.

## Módulos Disponibles

| Módulo | Versión | Descripción |
|--------|---------|-------------|
| [l10n_py](l10n_py/) | 16.0.1.1.0 | Plan de Cuentas Paraguay (RG 49/14) — 222 cuentas, 6 impuestos, 45+ grupos contables |
| [l10n_py_base](l10n_py_base/) | 16.0.1.2.0 | Datos base: departamentos, ciudades, barrios, validación RUC, extensión de partner |
| [l10n_py_account](l10n_py_account/) | 16.0.2.0.0 | Timbrado (autorización SET), numeración, fórmulas IVA SIFEN, datos demo |
| [l10n_py_edi_base](l10n_py_edi_base/) | 16.0.2.1.0 | Core EDI: CDC, KuDE, documentos asociados, inutilización, ciclo de vida DTE |
| [l10n_py_edi_factpy](l10n_py_edi_factpy/) | 16.0.1.2.0 | Conector EDI para proveedor FactPy |
| [l10n_py_edi_facturasend](l10n_py_edi_facturasend/) | 16.0.1.2.0 | Conector EDI para proveedor FacturaSend |

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
```

### Instalación de módulos

```bash
# Instalar toda la localización con facturación electrónica
odoo-bin -d mi_base -i l10n_py,l10n_py_base,l10n_py_account,l10n_py_edi_base --stop-after-init

# Instalar conector EDI (elegir uno)
odoo-bin -d mi_base -i l10n_py_edi_factpy --stop-after-init
# o
odoo-bin -d mi_base -i l10n_py_edi_facturasend --stop-after-init
```

### Con Doodba (Docker)

```bash
invoke install -m l10n_py,l10n_py_base,l10n_py_account,l10n_py_edi_base
invoke test -m l10n_py_account,l10n_py_edi_base
```

## Normativas Implementadas

- **RG 49/14** — Plan de Cuentas oficial del Ministerio de Hacienda
- **Decreto 7.795/2017** — Sistema Integrado de Facturación Electrónica Nacional (SIFEN)
- **MT SIFEN v150** — Manual Técnico del SIFEN versión 150
- **Ley 6.380/2019** — Modernización y simplificación del sistema tributario
- **RG 90/2021** — Formato Marangatú para libros IVA (planificado)

## Roadmap

Consulte [PRD_TAREFAS_PENDENTES.md](PRD_TAREFAS_PENDENTES.md) para el detalle
completo de funcionalidades pendientes con especificaciones BDD (Gherkin),
incluyendo:

- Emisión en lote, B2G, nominación obligatoria (RF-01)
- Eventos SIFEN: transporte, conformidad, cancelación con plazos (RF-06)
- Recibo electrónico y comprobantes de retención (RF-07)
- Libro IVA Ventas/Compras, exportación Marangatú, dashboard (RF-10)
- Contingencia avanzada con backoff exponencial (RF-12)

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

La OCA (Odoo Community Association) es una organización sin fines de lucro cuya
misión es apoyar el desarrollo colaborativo de las funcionalidades de Odoo y
promover su uso generalizado.

## Licencia

[LGPL-3](LICENSE)
