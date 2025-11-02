# Integración de Facturación Electrónica Paraguay con Odoo

## 📋 Descripción

Este proyecto implementa la integración de facturación electrónica del Paraguay (SIFEN -
Sistema Integrado de Facturación Electrónica Nacional) con Odoo 17, permitiendo la
emisión de documentos electrónicos conforme a las normativas de la SET (Subsecretaría de
Estado de Tributación).

## 🏗️ Arquitectura

El sistema está diseñado con una arquitectura modular:

```
├── l10n_py_edi_base/          # Módulo base con modelos y lógica común
├── l10n_py_edi_factpy/        # Conector para FactPy
└── l10n_py_edi_facturasend/   # Conector para FacturaSend
```

## 📁 Archivos Incluidos

- `paraguay_edi_integration_plan.md` - Plan detallado de desarrollo
- `l10n_py_edi_base_manifest.py` - Archivo de manifiesto del módulo base
- `l10n_py_edi_base_account_move.py` - Extensión del modelo de facturas
- `l10n_py_edi_base_res_partner.py` - Extensión del modelo de contactos
- `facturasend_connector.py` - Implementación del conector FacturaSend

## 🚀 Instalación

### Prerequisitos

1. **Odoo 17** instalado y funcionando
2. **Módulo de localización paraguaya** (`l10n_py`)
3. **Python 3.8+** con las siguientes librerías:

```bash
pip install qrcode[pil] requests cryptography reportlab
```

### Pasos de Instalación

1. **Copiar los módulos al directorio de addons de Odoo:**

```bash
cp -r l10n_py_edi_* /path/to/odoo/addons/
```

2. **Actualizar la lista de aplicaciones en Odoo:**

   - Ir a Aplicaciones → Actualizar Lista de Aplicaciones
   - Activar modo desarrollador si es necesario

3. **Instalar el módulo base:**

   - Buscar "Paraguay - Electronic Invoicing Base"
   - Instalar

4. **Instalar el conector deseado:**
   - Para FacturaSend: "Paraguay - FacturaSend Connector"
   - Para FactPy: "Paraguay - FactPy Connector"

## ⚙️ Configuración

### 1. Configuración de la Empresa

```
Ajustes → Compañías → [Su Compañía]
```

- **RUC**: Ingresar RUC de la empresa
- **Datos de ubicación**: Departamento, distrito, ciudad
- **Actividad económica**: Código de actividad principal

### 2. Configuración del Diario

```
Contabilidad → Configuración → Diarios
```

Para cada punto de venta:

- **Establecimiento**: 001
- **Punto de Expedición**: 001
- **Timbrado**: Número de timbrado vigente
- **Fecha Vencimiento Timbrado**: Fecha límite

### 3. Configuración del Proveedor EDI

```
Ajustes → Técnico → Parámetros del Sistema
```

#### Para FacturaSend:

- **l10n_py.edi_provider**: facturasend
- **l10n_py.facturasend.api_key**: [Su API Key]
- **l10n_py.facturasend.tenant_id**: [Su Tenant ID]
- **l10n_py.edi_environment**: test o prod

#### Para FactPy:

- **l10n_py.edi_provider**: factpy
- **l10n_py.factpy.api_key**: [Su API Key]
- **l10n_py.factpy.api_secret**: [Su API Secret]
- **l10n_py.edi_environment**: test o prod

### 4. Configuración de Productos

Para cada producto:

- **Código NCM**: Nomenclatura común del Mercosur (8 dígitos)
- **Unidad de Medida**: Según tabla SET

### 5. Configuración de Clientes

Datos obligatorios:

- **RUC** (para contribuyentes)
- **Tipo de Documento** y **Número** (para no contribuyentes)
- **Dirección completa**
- **Departamento, Distrito, Ciudad**

## 📊 Uso del Sistema

### Emisión de Factura Electrónica

1. **Crear factura normal en Odoo**
2. **Revisar campos EDI** en la pestaña "Facturación Electrónica"
3. **Confirmar la factura**
4. **Click en "Enviar a EDI"**
5. **El sistema automáticamente:**
   - Valida los datos
   - Genera el JSON
   - Envía al proveedor EDI
   - Recibe y almacena CDC, QR, XML
   - Genera el KUDE (PDF)

### Estados del Documento

- `draft` - Borrador
- `to_send` - Pendiente de envío
- `sent` - Enviado al proveedor
- `processing` - En proceso
- `accepted` - Aceptado por SET
- `rejected` - Rechazado
- `cancelled` - Cancelado
- `error` - Error en el proceso

### Consulta de Estado

```python
# Desde el botón en la factura
factura.action_check_edi_status()

# Proceso automático cada hora
Configuración → Técnico → Automatización → Acciones Planificadas
```

## 🧪 Testing

### Ambiente de Pruebas

1. Configurar `l10n_py.edi_environment = 'test'`
2. Usar credenciales de prueba del proveedor
3. Los CDCs generados en prueba no son válidos fiscalmente

### Tests Unitarios

```bash
# Ejecutar tests del módulo
./odoo-bin -c odoo.conf -u l10n_py_edi_base --test-enable --stop-after-init
```

### Validaciones Incluidas

- ✅ Validación de RUC con dígito verificador
- ✅ Validación de campos obligatorios
- ✅ Validación de NCM en productos
- ✅ Validación de timbrado vigente
- ✅ Validación de formato de datos

## 🔍 Troubleshooting

### Error: "RUC inválido"

- Verificar formato: XXXXXXXX-X
- Verificar dígito verificador
- El RUC debe estar activo en SET

### Error: "Timbrado vencido"

- Actualizar timbrado en configuración del diario
- Solicitar nuevo timbrado a SET

### Error: "NCM no especificado"

- Completar código NCM en todos los productos
- Usar tabla oficial de NCM del Mercosur

### Error de conexión

- Verificar credenciales API
- Verificar conectividad de red
- Revisar logs en: `Facturación → EDI → Logs`

## 📚 Documentación Adicional

### Enlaces Oficiales

- [SET - Facturación Electrónica](https://ekuatia.set.gov.py/)
- [Manual SIFEN](https://ekuatia.set.gov.py/portal/ekuatia/manual)
- [Documentación FacturaSend](https://facturasend.com.py/documentacion/)
- [Documentación FactPy](https://docs.factpy.com/)

### Estructura de Datos

Ver `paraguay_edi_integration_plan.md` para:

- Mapeo completo de campos
- Flujos de procesamiento
- Especificaciones técnicas

## 🤝 Soporte

Para soporte técnico:

1. Revisar documentación incluida
2. Consultar logs del sistema
3. Contactar al proveedor EDI
4. Abrir issue en el repositorio

## 📄 Licencia

Este proyecto está bajo licencia LGPL-3.

## 🔄 Actualizaciones

### Versión 1.0.0 (Actual)

- ✅ Soporte para Factura Electrónica
- ✅ Soporte para Nota de Crédito
- ✅ Soporte para Nota de Débito
- ✅ Integración con FacturaSend
- ✅ Generación de QR y KUDE

### Próximas Versiones

- [ ] Nota de Remisión Electrónica
- [ ] Autofactura Electrónica
- [ ] Consulta de RUC en línea
- [ ] Reportes de control fiscal
- [ ] Integración con contabilidad
- [ ] Módulo de contingencia avanzado
- [ ] API de consulta de estado automática
- [ ] Generación de código QR nativo

## 💡 Tips de Implementación

1. **Comenzar en ambiente de pruebas** hasta dominar el flujo
2. **Validar datos maestros** antes de emitir documentos
3. **Configurar backups** de XMLs y CDCs
4. **Monitorear logs** regularmente
5. **Mantener timbrados actualizados**
6. **Capacitar usuarios** en el nuevo flujo

---

**Nota:** Este es un proyecto en desarrollo. Asegúrese de cumplir con todas las
normativas fiscales vigentes en Paraguay antes de usar en producción.
