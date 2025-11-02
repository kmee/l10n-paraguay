# Paraguay - Base Localization

Módulo base de localización para Paraguay compatible con Odoo 17.0.

## Características

### 🏛️ Estructura Administrativa
- **Departamentos**: 17 departamentos usando `res.country.state` del core
- **Distritos**: Nivel intermedio específico de Paraguay (modelo personalizado)
- **Ciudades**: Usando `res.city` del core con extensiones

### 📝 Datos Fiscales
- **RUC**: Registro Único del Contribuyente con cálculo automático de dígito verificador
- **Tipos de Contribuyente**: Contribuyente / No Contribuyente
- **Tipos de Documento**: Cédula paraguaya, Pasaporte, Cédula extranjera, etc.

### 📍 Códigos SET
Todos los niveles administrativos incluyen códigos oficiales de la Subsecretaría de Estado de Tributación (SET):
- Código de Departamento (1-17)
- Código de Distrito (XXYY)
- Código de Ciudad (XXYYZZ)

### 🔗 Integración con Core
Usa modelos estándar de Odoo mediante `base_address_extended`:
- `res.country.state` para departamentos
- `res.city` para ciudades
- Jerarquía automática y validaciones

## Instalación

### Dependencias

```python
'depends': [
    'base',
    'base_address_extended',
]
```

### Pasos

1. Copiar el módulo a la carpeta de addons
2. Actualizar la lista de módulos
3. Instalar el módulo `l10n_py_base`

## Uso

### Crear un Partner con Ubicación

```python
partner = self.env['res.partner'].create({
    'name': 'Empresa Ejemplo S.A.',
    'is_company': True,
    'country_id': self.env.ref('base.py').id,
    'state_id': self.env.ref('l10n_py_base.state_py_central').id,
    'l10n_py_district_id': self.env.ref('l10n_py_base.district_asuncion').id,
    'city_id': self.env.ref('l10n_py_base.city_asuncion').id,
    'l10n_py_taxpayer_type': '1',
    'l10n_py_ruc': '80012345',
})

# Códigos SET se calculan automáticamente
print(partner.l10n_py_department_code)  # 11
print(partner.l10n_py_district_code)    # 1101
print(partner.l10n_py_city_code)        # 110101
```

### Validar RUC

```python
from odoo.addons.l10n_py_base.validators.ruc_validator import RUCValidator

# Validar RUC
is_valid, error_msg = RUCValidator.validate('80012345')

# Calcular dígito verificador
dv = RUCValidator.get_check_digit('80012345')

# Obtener número limpio
ruc_number = RUCValidator.get_ruc_number('80012345-6')
```

## Estructura de Datos

### Jerarquía Administrativa

```
res.country (Paraguay - PY)
  │
  ├── res.country.state (Departamento: Central)
  │   │   Campo adicional: l10n_py_code = 11
  │   │
  │   ├── l10n_py.district (Distrito: Asunción)
  │   │   │   code = 1101
  │   │   │
  │   │   └── res.city (Ciudad: Asunción)
  │   │       │   Campo adicional: l10n_py_code = 110101
  │   │       │   Campo adicional: l10n_py_district_id
  │   │
  │   └── l10n_py.district (Distrito: San Lorenzo)
  │       └── res.city (Ciudad: San Lorenzo)
  │
  └── res.country.state (Departamento: Alto Paraná)
      └── ...
```

### Campos en res.partner

**Identificación Fiscal:**
- `l10n_py_taxpayer_type`: Tipo de contribuyente (1=Contribuyente, 2=No Contribuyente)
- `l10n_py_ruc`: RUC sin dígito verificador (8 dígitos)
- `l10n_py_dv`: Dígito verificador (calculado)
- `l10n_py_ruc_full`: RUC completo con DV (formato: XXXXXXXX-Y)
- `l10n_py_document_type`: Tipo de documento de identidad
- `l10n_py_document_number`: Número de documento

**Ubicación (editables):**
- `state_id`: Departamento (Many2one a res.country.state)
- `l10n_py_district_id`: Distrito (Many2one a l10n_py.district)
- `city_id`: Ciudad (Many2one a res.city)
- `street_number`: Número de casa

**Códigos SET (calculados automáticamente):**
- `l10n_py_department_code`: Código del departamento (related)
- `l10n_py_district_code`: Código del distrito (related)
- `l10n_py_city_code`: Código de la ciudad (related)

**Información Adicional:**
- `l10n_py_trade_name`: Nombre comercial o fantasía
- `l10n_py_economic_activity`: Código de actividad económica
- `l10n_py_is_diplomatic`: Indicador de status diplomático
- `l10n_py_dncp`: Indicador DNCP (0=Normal, 1=Estado)

## Departamentos de Paraguay

| Código | Nombre              | Code   |
|--------|---------------------|--------|
| 1      | Concepción          | PY-1   |
| 2      | San Pedro           | PY-2   |
| 3      | Cordillera          | PY-3   |
| 4      | Guairá              | PY-4   |
| 5      | Caaguazú            | PY-5   |
| 6      | Caazapá             | PY-6   |
| 7      | Itapúa              | PY-7   |
| 8      | Misiones            | PY-8   |
| 9      | Paraguarí           | PY-9   |
| 10     | Alto Paraná         | PY-10  |
| 11     | Central             | PY-11  |
| 12     | Ñeembucú            | PY-12  |
| 13     | Amambay             | PY-13  |
| 14     | Canindeyú           | PY-14  |
| 15     | Presidente Hayes    | PY-15  |
| 16     | Boquerón            | PY-16  |
| 17     | Alto Paraguay       | PY-17  |
| -      | Asunción (Capital)  | PY-ASU |

## Validaciones

### Validación de RUC
- Formato numérico de 6-8 dígitos
- Cálculo de dígito verificador usando módulo 11
- Obligatorio para contribuyentes

### Validación de Documentos
- Cédula paraguaya: solo números
- Validación según tipo de documento

### Validación de Ubicación
- Jerarquía departamento → distrito → ciudad validada automáticamente
- Departamento obligatorio para clientes paraguayos en facturación electrónica

## Métodos Útiles

### res.partner

```python
# Validar todos los datos fiscales
partner.validate_fiscal_data()

# Validar con SET (preparado para integración futura)
partner.action_validate_with_set()

# Crear desde RUC (preparado para integración con servicio externo)
partner = self.env['res.partner'].create_from_ruc('80012345')
```

### RUCValidator

```python
from odoo.addons.l10n_py_base.validators.ruc_validator import RUCValidator

# Validar RUC
is_valid, error_msg = RUCValidator.validate(ruc)

# Obtener dígito verificador
dv = RUCValidator.get_check_digit(ruc)

# Validar RUC completo (con DV)
is_valid = RUCValidator.validate_full(ruc_with_dv)

# Limpiar formato
ruc_number = RUCValidator.get_ruc_number(ruc_string)
```

## Comportamiento Automático (onchange)

### Selección de Ciudad
Al seleccionar una ciudad, el distrito y departamento se llenan automáticamente.

### Selección de Distrito
Al seleccionar un distrito, el departamento se actualiza automáticamente.

### Cambio de Departamento
Al cambiar el departamento, el distrito y ciudad se limpian si no pertenecen al nuevo departamento.

### Ingreso de RUC
Al ingresar un RUC:
- Se normaliza el formato
- Se calcula el dígito verificador
- Se marca automáticamente como contribuyente

## Integración con EDI

Este módulo es la base para los módulos de facturación electrónica:
- `l10n_py_account`: Extensiones contables
- `l10n_py_edi_base`: Base de facturación electrónica
- `l10n_py_edi_factpy`: Integración con FactPy
- `l10n_py_edi_facturasend`: Integración con FacturaSend

Los códigos SET están disponibles para integración EDI:
```python
customer_data = {
    'departamento': partner.l10n_py_department_code,
    'distrito': partner.l10n_py_district_code,
    'ciudad': partner.l10n_py_city_code,
}
```

## Extender Datos

### Agregar Más Distritos

Crear archivo XML en `data/`:

```xml
<record id="district_nuevo" model="l10n_py.district">
    <field name="code">1106</field>
    <field name="name">Nuevo Distrito</field>
    <field name="state_id" ref="state_py_central"/>
</record>
```

### Agregar Más Ciudades

```xml
<record id="city_nueva" model="res.city">
    <field name="name">Nueva Ciudad</field>
    <field name="state_id" ref="state_py_central"/>
    <field name="country_id" ref="base.py"/>
    <field name="l10n_py_code">110601</field>
    <field name="l10n_py_district_id" ref="district_nuevo"/>
</record>
```

## Documentación

- [MIGRACAO_BASE_ADDRESS_EXTENDED.md](MIGRACAO_BASE_ADDRESS_EXTENDED.md): Documentación técnica de la migración
- [EXEMPLOS_USO.md](EXEMPLOS_USO.md): Ejemplos de uso prácticos

## Autor

**KMEE**
- Website: https://github.com/kmee

## Licencia

LGPL-3

## Versión

17.0.1.0.0

## Changelog

### 17.0.1.0.0
- Refactorización para usar `base_address_extended`
- Migración de modelos personalizados a extensiones del core
- Mejora de UX con widgets de selección
- Validación automática de jerarquía administrativa
- Documentación completa

