# Refatoração para usar base_address_extended

## Objetivo

Refatorar a implementação de localização paraguaya para usar os modelos estándar del
core de Odoo (`res.country.state` y `res.city`) en lugar de modelos personalizados,
siguiendo las mejores prácticas de Odoo.

## Resumen de Cambios

### Módulo: l10n_py_base

#### 1. Dependencias Actualizadas

- Agregado: `base_address_extended`
- Ahora depende de: `['base', 'base_address_extended']`

#### 2. Modelos Nuevos/Modificados

**Creados:**

- `models/res_country_state.py`: Extensión de `res.country.state` con campo
  `l10n_py_code`
- `models/res_city.py`: Extensión de `res.city` con campos `l10n_py_code` y
  `l10n_py_district_id`

**Modificados:**

- `models/l10n_py_district.py`: Ahora relaciona con `res.country.state` en lugar de
  `l10n_py.department`
- `models/res_partner.py`: Refactorizado para usar `state_id`, `city_id` y
  `l10n_py_district_id`

**Eliminados:**

- `models/l10n_py_department.py` → Reemplazado por extensión de `res.country.state`
- `models/l10n_py_city.py` → Reemplazado por extensión de `res.city`

#### 3. Datos

**Nuevos archivos:**

- `data/res_country_state_data.xml`: 17 departamentos + Asunción
- `data/l10n_py_district_data.xml`: Distritos principales
- `data/res_city_data.xml`: Ciudades principales

**Archivos eliminados:**

- `data/l10n_py_departments.xml`
- `data/l10n_py_districts.xml`
- `data/l10n_py_cities.xml`

#### 4. Cambios en res.partner

**Campos antes:**

```python
l10n_py_department_code = fields.Integer()  # Editable
l10n_py_department_name = fields.Char(computed=True)
l10n_py_district_code = fields.Integer()  # Editable
l10n_py_district_name = fields.Char(computed=True)
l10n_py_city_code = fields.Integer()  # Editable
l10n_py_city_name = fields.Char(computed=True)
```

**Campos ahora:**

```python
# Campos principales (editables)
state_id = Many2one('res.country.state')  # Del core
l10n_py_district_id = Many2one('l10n_py.district')
city_id = Many2one('res.city')  # Del core

# Códigos SET (solo lectura, computados)
l10n_py_department_code = Integer(related='state_id.l10n_py_code')
l10n_py_district_code = Integer(related='l10n_py_district_id.code')
l10n_py_city_code = Integer(related='city_id.l10n_py_code')
```

**Nuevos métodos onchange:**

- `_onchange_state_id()`: Limpia distrito y ciudad al cambiar departamento
- `_onchange_district_id()`: Actualiza departamento y filtra ciudades
- `_onchange_city_id()`: Actualiza distrito y departamento automáticamente

#### 5. Vistas Actualizadas

- `views/res_partner_views.xml`: Ahora usa widgets de selección para `state_id`,
  `l10n_py_district_id` y `city_id`
- Los códigos SET se muestran en grupo separado de solo lectura
- Filtros dinámicos basados en jerarquía

### Módulo: l10n_py_edi_base

#### Cambios en res.company

Los campos de ubicación ahora son relacionados al partner de la compañía:

```python
l10n_py_department_code = Integer(related='partner_id.l10n_py_department_code')
l10n_py_district_code = Integer(related='partner_id.l10n_py_district_code')
l10n_py_city_code = Integer(related='partner_id.l10n_py_city_code')
```

#### Archivos de datos eliminados

- `data/l10n_py_departments.xml` (duplicado de l10n_py_base)
- `data/l10n_py_districts.xml` (duplicado de l10n_py_base)
- `data/l10n_py_cities.xml` (duplicado de l10n_py_base)

## Jerarquía de Ubicación

```
res.country (Paraguay - PY)
  │
  ├── res.country.state (Departamento: Central, código SET: 11)
  │   │
  │   ├── l10n_py.district (Distrito: Asunción, código: 1101)
  │   │   │
  │   │   └── res.city (Ciudad: Asunción, código SET: 110101)
  │   │
  │   ├── l10n_py.district (Distrito: San Lorenzo, código: 1102)
  │   │   │
  │   │   └── res.city (Ciudad: San Lorenzo, código SET: 110201)
  │   │
  │   └── ...
  │
  ├── res.country.state (Departamento: Alto Paraná, código SET: 10)
  │   └── ...
  │
  └── ...
```

## Ventajas de la Nueva Implementación

1. **Compatibilidad con el Core**: Usa modelos estándar de Odoo
2. **Interoperabilidad**: Compatible con otros módulos que usan `base_address_extended`
3. **Mejor UX**: Widgets de selección con búsqueda y autocompletado
4. **Mantenibilidad**: Menos código personalizado
5. **Consistencia Automática**: Los onchange mantienen la jerarquía
6. **Códigos SET Preservados**: Disponibles como campos relacionados

## Compatibilidad

- **Versión de Odoo**: 17.0
- **Módulos Requeridos**: `base`, `base_address_extended`
- **Módulos Compatibles**: `l10n_py_account`, `l10n_py_edi_base`, `l10n_py_edi_factpy`

## Migración desde Versión Anterior

Para migrar datos existentes:

1. Los departamentos en `l10n_py.department` deben migrarse a `res.country.state`
2. Los distritos deben actualizarse para referenciar `res.country.state`
3. Las ciudades en `l10n_py.city` deben migrarse a `res.city`
4. Los partners deben actualizarse:
   - Convertir códigos a relaciones: `l10n_py_department_code` → `state_id`
   - Convertir códigos a relaciones: `l10n_py_district_code` → `l10n_py_district_id`
   - Convertir códigos a relaciones: `l10n_py_city_code` → `city_id`

**Nota**: Los códigos SET se recalcularán automáticamente como campos relacionados.

## Archivos Afectados

### l10n_py_base

**Creados**:

- `models/res_country_state.py`
- `models/res_city.py`
- `data/res_country_state_data.xml`
- `data/l10n_py_district_data.xml`
- `data/res_city_data.xml`
- `MIGRACAO_BASE_ADDRESS_EXTENDED.md`

**Modificados**:

- `__manifest__.py`
- `models/__init__.py`
- `models/l10n_py_district.py`
- `models/res_partner.py`
- `views/res_partner_views.xml`
- `security/ir.model.access.csv`

**Eliminados**:

- `models/l10n_py_department.py`
- `models/l10n_py_city.py`
- `data/l10n_py_departments.xml`
- `data/l10n_py_districts.xml`
- `data/l10n_py_cities.xml`

### l10n_py_edi_base

**Modificados**:

- `models/res_company.py`

**Eliminados**:

- `data/l10n_py_departments.xml`
- `data/l10n_py_districts.xml`
- `data/l10n_py_cities.xml`

## Comportamiento del Usuario

### Antes

1. El usuario ingresaba manualmente códigos numéricos
2. Los nombres se calculaban automáticamente
3. No había validación de jerarquía
4. Podían existir inconsistencias

### Ahora

1. El usuario selecciona de listas desplegables
2. Los códigos SET se calculan automáticamente
3. La jerarquía se valida automáticamente
4. Al seleccionar una ciudad, el distrito y departamento se llenan automáticamente
5. Mejor experiencia de usuario con búsqueda y autocompletado

## Ejemplo de Uso en EDI

Los campos siguen estando disponibles para EDI:

```python
# En account.move._prepare_customer_data()
customer_data = {
    'departamento': partner.l10n_py_department_code,  # Código SET
    'distrito': partner.l10n_py_district_code,  # Código SET
    'ciudad': partner.l10n_py_city_code,  # Código SET
    # ...
}
```

Los códigos SET se obtienen automáticamente de las relaciones.

## Próximos Pasos

1. ✅ Refactorización completada
2. ⏳ Crear script de migración para datos existentes
3. ⏳ Agregar más distritos y ciudades según necesidad
4. ⏳ Probar integración con módulos EDI
5. ⏳ Documentar proceso de migración para usuarios

## Notas Técnicas

- El distrito (`l10n_py.district`) se mantiene como modelo personalizado porque no
  existe equivalente en el core de Odoo
- Los códigos SET son únicos por país (constraint SQL)
- Los datos se cargan con `noupdate="1"` para permitir personalización
- La jerarquía departamento → distrito → ciudad se valida en los onchange
