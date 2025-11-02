# Migración a base_address_extended

## Resumen

Este documento describe la refactorización del módulo `l10n_py_base` para usar los modelos estándar del core de Odoo en lugar de modelos personalizados para ubicaciones.

## Cambios Realizados

### 1. Dependencias

**Antes:**
```python
'depends': ['base']
```

**Después:**
```python
'depends': ['base', 'base_address_extended']
```

### 2. Modelos de Ubicación

#### Departamentos
- **Antes:** Modelo personalizado `l10n_py.department`
- **Después:** Extensión de `res.country.state` con campo `l10n_py_code`
- **Archivo:** `models/res_country_state.py`

#### Ciudades
- **Antes:** Modelo personalizado `l10n_py.city`
- **Después:** Extensión de `res.city` con campos `l10n_py_code` y `l10n_py_district_id`
- **Archivo:** `models/res_city.py`

#### Distritos
- **Antes:** `l10n_py.district` con relación a `l10n_py.department`
- **Después:** `l10n_py.district` con relación a `res.country.state`
- **Archivo:** `models/l10n_py_district.py`
- **Nota:** Se mantiene como modelo personalizado porque no existe equivalente en el core de Odoo

### 3. Modelo res.partner

#### Campos Modificados

**Antes:**
```python
l10n_py_department_code = fields.Integer(...)  # Campo editable
l10n_py_department_name = fields.Char(computed=True)
l10n_py_district_code = fields.Integer(...)  # Campo editable
l10n_py_district_name = fields.Char(computed=True)
l10n_py_city_code = fields.Integer(...)  # Campo editable
l10n_py_city_name = fields.Char(computed=True)
```

**Después:**
```python
# Campos relacionales principales (editables)
state_id = Many2one('res.country.state')  # Del core (base_address_extended)
l10n_py_district_id = Many2one('l10n_py.district')
city_id = Many2one('res.city')  # Del core (base_address_extended)

# Códigos SET de solo lectura (computados)
l10n_py_department_code = Integer(related='state_id.l10n_py_code')
l10n_py_district_code = Integer(related='l10n_py_district_id.code')
l10n_py_city_code = Integer(related='city_id.l10n_py_code')
```

#### Nuevos Métodos Onchange

Se agregaron métodos para mantener consistencia en la jerarquía:
- `_onchange_state_id`: Limpia distrito y ciudad cuando cambia el departamento
- `_onchange_district_id`: Actualiza departamento y filtra ciudades
- `_onchange_city_id`: Actualiza distrito y departamento automáticamente

### 4. Datos

#### Departamentos
- **Archivo anterior:** `data/l10n_py_departments.xml`
- **Archivo nuevo:** `data/res_country_state_data.xml`
- **Modelo:** `res.country.state`
- **Registros:** 17 departamentos + Asunción como distrito especial

#### Distritos
- **Archivo anterior:** `data/l10n_py_districts.xml`
- **Archivo nuevo:** `data/l10n_py_district_data.xml`
- **Modelo:** `l10n_py.district`
- **Cambio:** Relación cambió de `department_id` a `state_id`

#### Ciudades
- **Archivo anterior:** `data/l10n_py_cities.xml`
- **Archivo nuevo:** `data/res_city_data.xml`
- **Modelo:** `res.city`
- **Campos adicionales:** `l10n_py_code`, `l10n_py_district_id`

### 5. Vistas

**Cambios en `views/res_partner_views.xml`:**
- Ahora usa widgets de selección para `state_id`, `l10n_py_district_id` y `city_id`
- Los códigos SET se muestran como campos de solo lectura
- Filtros dinámicos basados en jerarquía (distrito depende de state_id, city depende de state_id)

### 6. Seguridad

**Archivo:** `security/ir.model.access.csv`
- Eliminadas reglas para `l10n_py.department` y `l10n_py.city`
- Mantenidas reglas para `l10n_py.district`
- Las reglas para `res.country.state` y `res.city` ya existen en el core

## Ventajas de la Nueva Implementación

1. **Compatibilidad con el Core**: Usa modelos estándar de Odoo
2. **Mejor Integración**: Compatible con otros módulos que usan `base_address_extended`
3. **Interfaz Mejorada**: Widgets de selección con búsqueda
4. **Mantenibilidad**: Menos modelos personalizados que mantener
5. **Jerarquía Automática**: Los onchange mantienen consistencia automáticamente
6. **Códigos SET Preservados**: Se mantienen como campos relacionados de solo lectura

## Estructura de Jerarquía

```
res.country (País: Paraguay)
  └── res.country.state (Departamento: Central)
      ├── l10n_py.district (Distrito: Asunción)
      │   └── res.city (Ciudad: Asunción)
      ├── l10n_py.district (Distrito: San Lorenzo)
      │   └── res.city (Ciudad: San Lorenzo)
      └── ...
```

## Migración de Datos Existentes

Para bases de datos existentes, se necesitará crear un script de migración que:

1. Migre departamentos de `l10n_py.department` a `res.country.state`
2. Actualice distritos para referenciar `res.country.state`
3. Migre ciudades de `l10n_py.city` a `res.city`
4. Actualice partners existentes:
   - Mapear `l10n_py_department_code` a `state_id`
   - Mapear `l10n_py_district_code` a `l10n_py_district_id`
   - Mapear `l10n_py_city_code` a `city_id`

## Archivos Modificados

### Creados
- `models/res_country_state.py`
- `models/res_city.py`
- `data/res_country_state_data.xml`
- `data/l10n_py_district_data.xml`
- `data/res_city_data.xml`

### Modificados
- `__manifest__.py`
- `models/__init__.py`
- `models/l10n_py_district.py`
- `models/res_partner.py`
- `views/res_partner_views.xml`
- `security/ir.model.access.csv`

### Eliminados
- `models/l10n_py_department.py`
- `models/l10n_py_city.py`
- `data/l10n_py_departments.xml`
- `data/l10n_py_districts.xml` (renombrado)
- `data/l10n_py_cities.xml`

## Compatibilidad

- **Odoo Version:** 17.0
- **Módulos Requeridos:** `base`, `base_address_extended`
- **Compatible con:** Otros módulos de localización paraguaya (`l10n_py_account`, `l10n_py_edi_base`)

## Notas Importantes

1. Los códigos SET se preservan y están disponibles como campos relacionados
2. La jerarquía departamento > distrito > ciudad se mantiene intacta
3. El distrito es específico de Paraguay y no tiene equivalente en el core
4. Los datos de ejemplo incluyen solo el departamento Central; se pueden agregar más según necesidad

