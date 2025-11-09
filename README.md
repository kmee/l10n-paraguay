# 🇵🇾 Plano de Contas - Paraguay (Odoo 16)

**Localización contable para Paraguay basada en la Resolución General N° 49/14**

## 📋 Índice

- [Descripción](#descripción)
- [Características](#características)
- [Instalación](#instalación)
- [Estructura](#estructura)
- [Verificación](#verificación)
- [Problemas Conocidos](#problemas-conocidos)
- [Soporte](#soporte)

## Descripción

Módulo de localización contable para Paraguay que implementa el Plan de Cuentas oficial según la **Resolución General N° 49/14** del Ministerio de Hacienda.

### Características Principales

- ✅ **222 Cuentas Contables** organizadas jerárquicamente
- ✅ **45+ Grupos Contables** para estructura completa
- ✅ **6 Impuestos** preconfigurados (IVA 10%, 5%, Exento)
- ✅ **3 Grupos de Impuestos** (IVA 10%, IVA 5%, Exento)
- ✅ **Configuración Automática** de cuentas por defecto
- ✅ **Moneda Nacional** PYG (Guaraní)

## Características

### Cuentas Contables

```
📊 Estructura Jerárquica (4 niveles)
├── 1. ACTIVO
│   ├── 1.01. ACTIVO CORRIENTE
│   │   ├── 1.01.01. DISPONIBILIDADES
│   │   │   ├── 1.01.01.01 Recaudaciones a depositar
│   │   │   ├── 1.01.01.02 Caja
│   │   │   └── ...
│   │   └── ...
│   └── 1.02. ACTIVO NO CORRIENTE
├── 2. PASIVO
│   ├── 2.01. PASIVO CORRIENTE
│   └── 2.02. PASIVO NO CORRIENTE
├── 3. PATRIMONIO NETO
│   ├── 3.01. CAPITAL
│   ├── 3.02. RESERVAS
│   └── 3.03. RESULTADOS
├── 4. INGRESOS OPERATIVOS
├── 5. COSTOS DE VENTAS
├── 7. INGRESOS POR ACTIVOS BIOLÓGICOS
└── 8-19. OTROS INGRESOS Y GASTOS
```

### Impuestos Configurados

| Impuesto | Tasa | Tipo | Descripción |
|----------|------|------|-------------|
| IVA Venta 10% | 10% | Venta | IVA tasa general |
| IVA Venta 5% | 5% | Venta | IVA tasa reducida |
| Exento | 0% | Venta | Operaciones exentas |
| IVA Compra 10% | 10% | Compra | IVA tasa general |
| IVA Compra 5% | 5% | Compra | IVA tasa reducida |
| Exento Compra | 0% | Compra | Operaciones exentas |

## Instalación

### Método 1: Via Interface (Recomendado)

1. Activar modo desarrollador
2. Ir a **Aplicaciones**
3. Buscar `l10n_py`
4. Clic en **Instalar**

### Método 2: Via Línea de Comandos

```bash
# Instalar el módulo
odoo-bin -d su_base_datos -i l10n_py --stop-after-init

# Actualizar el módulo (si ya está instalado)
odoo-bin -d su_base_datos -u l10n_py --stop-after-init
```

### Método 3: Instalación Automática

El módulo se instala automáticamente al crear una empresa con país Paraguay (PY).

## Estructura

### Archivos de Datos

```
l10n_py/
├── data/
│   ├── account_tax_group_data.xml          # Grupos de impuestos
│   ├── account_chart_template_data.xml     # Template principal + impuestos
│   ├── account.account.template.csv        # 222 cuentas contables
│   ├── account_group.xml                   # 45+ grupos jerárquicos
│   ├── account_chart_template_account_account_link.xml  # Links de propiedades
│   └── account_chart_template_configure_data.xml        # Auto-instalación
├── security/
│   └── ir.model.access.csv                 # Permisos
└── __manifest__.py                         # Manifiesto del módulo
```

### Orden de Carga (IMPORTANTE)

Los archivos se cargan en este orden específico:

1. `account_tax_group_data.xml` - Grupos de impuestos primero
2. `account_chart_template_data.xml` - Template y impuestos
3. `account.account.template.csv` - Cuentas contables
4. `account_group.xml` - Grupos jerárquicos
5. `account_chart_template_account_account_link.xml` - Links de propiedades
6. `account_chart_template_configure_data.xml` - Configuración final

## Verificación

### Verificar Instalación

Después de instalar, verificar:

1. **Cuentas Contables**
   - Ir a: Contabilidad > Configuración > Plan de Cuentas
   - Verificar que existen ~227 cuentas (222 + 5 automáticas)

2. **Grupos Contables**
   - Ir a: Contabilidad > Configuración > Grupos de Cuentas
   - Verificar estructura jerárquica correcta

3. **Impuestos**
   - Ir a: Contabilidad > Configuración > Impuestos
   - Verificar 6 impuestos (3 venta + 3 compra)

### Scripts de Verificación

Se incluyen scripts para verificar la correcta instalación:

#### Verificación SQL

```bash
cd /ruta/a/l10n-paraguay
psql su_base_datos -f verificar_codigos.sql
```

#### Verificación Python

```bash
odoo shell -d su_base_datos
>>> exec(open('verificar_codigos.py').read())
```

## Problemas Conocidos

### 1. Cuentas Automáticas (NORMAL ✅)

El sistema crea automáticamente estas cuentas:

- `1.01.01.021` - Cash
- `1.01.01.031` - Liquidity Transfer
- `1.01.01.041` - Bank
- `999997` - Cash Discount Gain
- `999998` - Cash Discount Loss

**Esto es NORMAL** y necesario para el funcionamiento de Odoo.

### 2. Códigos en Trial Balance (INVESTIGAR ⚠️)

Algunos usuarios reportan que el Trial Balance muestra códigos con zeros extras:
- Muestra: `10.020` en lugar de `10.02`
- Muestra: `4.0300` en lugar de `4.03`
- Muestra: `190000` en lugar de `19`

**IMPORTANTE:** Los códigos en el CSV están correctos. Este puede ser:
- Problema de visualización del Odoo (solo visual)
- Problema de importación (datos incorrectos en BD)

**Solución:** Usar los scripts de verificación para determinar si es visual o real.

Para más detalles, ver:
- `ANALISE_TRIAL_BALANCE.md`
- `VERIFICACAO_CODIGOS.md`

## Configuración de Empresa

Al aplicar el plan de cuentas a una empresa, se configuran automáticamente:

- 💰 Cuenta de clientes: `1.01.03.01` - Deudores por ventas
- 💰 Cuenta de proveedores: `2.01.01.01` - Proveedores locales
- 📦 Cuenta de gastos: `5.01.01` - Costo de mercaderías
- 📦 Cuenta de ingresos: `4.01.01` - Ventas de mercaderías
- 💱 Cuenta de diferencia de cambio (ingreso): `8.05`
- 💱 Cuenta de diferencia de cambio (gasto): `13.04`
- 💵 Cuenta de efectivo: `1.01.01.02` - Caja
- 🏦 Cuenta bancaria: `1.01.01.04` - Bancos
- 🔄 Cuenta de transferencia: `1.01.01.03` - Fondos fijos

## Dependencias

```python
{
    'depends': [
        'account',  # Contabilidad base de Odoo
    ],
}
```

## Información del Módulo

- **Nombre Técnico:** `l10n_py`
- **Versión:** 16.0.1.0.0
- **Categoría:** Accounting/Localizations
- **Autor:** Tu Nombre / Empresa
- **Licencia:** LGPL-3
- **Moneda:** PYG (Guaraní Paraguayo)
- **País:** Paraguay (PY)

## Estructura de Códigos

El plan de cuentas utiliza códigos jerárquicos con puntos como separadores:

- **1 nivel:** `19` (Impuesto a la Renta)
- **2 niveles:** `10.02` (Comisiones sobre ventas)
- **3 niveles:** `10.01.01` (Sueldos y jornales)
- **4 niveles:** `1.01.01.01` (Recaudaciones a depositar)

**IMPORTANTE:** Se mantiene fidelidad al plan oficial, con niveles variables según la cuenta.

## Soporte

### Documentación Adicional

- `ANALISE_TRIAL_BALANCE.md` - Análisis del problema de visualización
- `VERIFICACAO_CODIGOS.md` - Guía de verificación detallada
- `verificar_codigos.sql` - Script SQL de verificación
- `verificar_codigos.py` - Script Python de verificación

### Reportar Problemas

Si encuentras problemas:

1. Ejecutar scripts de verificación
2. Revisar logs de instalación
3. Verificar que todos los archivos fueron cargados
4. Comparar con instalación limpia

### Referencias

- **Resolución General N° 49/14** - Ministerio de Hacienda
- **Plan de Cuentas Oficial** - Paraguay
- [Odoo Documentation](https://www.odoo.com/documentation/16.0/)

## Licencia

LGPL-3

---

**Última actualización:** 2025-11-08  
**Compatible con:** Odoo 16.0  
**Estado:** ✅ Funcional - Verificación pendiente de códigos
