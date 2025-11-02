# Usage

## Managing Partners

### Creating a Customer/Vendor

1. Go to **Contacts**
2. Click **Create**
3. Fill in basic information:
   - Name
   - Email, Phone
4. Fill Paraguayan fiscal data:
   - **Taxpayer Type**: Choose based on fiscal status
   - **Document Type**: Select appropriate type
   - **RUC**: If customer is a taxpayer
5. Complete address:
   - Select **Department**
   - Select **District** (filtered by department)
   - Select **City** (filtered by district)
6. Click **Save**

### Validating Fiscal Data

The system automatically validates:
- RUC format and verification digit
- Required fields based on taxpayer type
- Consistency between document types

Error messages will appear if validation fails.

## RUC Verification

### Understanding RUC Format

Format: XXXXXXXX-D
- First 8 digits: taxpayer number
- Last digit: verification digit (DV)

Example: 12345678-9

### Automatic Calculation

When entering a RUC without DV:
1. Enter the 8-digit number
2. System can calculate the DV automatically (if implemented)
3. Or enter complete RUC with DV for validation

## Taxpayer Types

### Contribuyente (Taxpayer)
- Must have valid RUC
- Subject to tax obligations
- Required for issuing/receiving tax documents

### No Contribuyente (Non-Taxpayer)
- May not have RUC
- Limited fiscal obligations
- Cannot receive electronic invoices (in most cases)

## Geographic Selection

### Selecting Locations

The location fields are cascading:
1. First select **Department**
2. Then **District** (list filters to show only districts in selected department)
3. Finally **City** (list filters to show only cities in selected district)

### Common Departments
- Asunción (capital)
- Central
- Alto Paraná
- Itapúa
- Others...

## Integration with Other Modules

This base module provides data for:
- `l10n_py`: Chart of accounts
- `l10n_py_account`: Accounting extensions
- `l10n_py_edi_base`: Electronic invoicing

All fiscal data entered here is used automatically by these modules.

