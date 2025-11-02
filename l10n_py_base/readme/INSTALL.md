# Installation

## Prerequisites

- Odoo 16.0
- `base` module (core Odoo)
- `base_address_extended` module

## Installation Steps

1. **Install Dependencies**:
   First ensure `base_address_extended` is installed:
   - Go to **Apps**
   - Search for "Base Address Extended"
   - Click **Install**

2. **Install Module**:
   - Go to **Apps**
   - Click **Update Apps List**
   - Search for "Paraguay - Base Localization"
   - Click **Install**

## Post-Installation

After installation:

1. **Verify Location Data**:
   - Go to **Settings > Technical > Localizations > Fed. States**
   - Verify Paraguayan departments are loaded
   - Check **Cities** for district and city data

2. **Configure Company**:
   - Go to **Settings > General Settings > Companies**
   - Edit your company
   - Fill in Paraguayan fiscal information

3. **Test Partner Creation**:
   - Create a test contact
   - Verify all fiscal fields are available
   - Test RUC validation

## Data Loaded

The module automatically loads:
- 17 Paraguayan departments (states)
- Districts (distritos) for each department
- Major cities across Paraguay

## Troubleshooting

### Location Data Not Showing

If departments/cities don't appear:
1. Verify module is fully installed
2. Check **Settings > Technical > Localizations > Fed. States**
3. Look for country "Paraguay" (PY)
4. Update module if needed

### RUC Validation Not Working

If RUC validation doesn't work:
1. Verify RUC format: XXXXXXXX-D
2. Check that all 9 characters are present
3. Ensure hyphen is included

## Dependencies

This module serves as base for:
- `l10n_py`: Accounting localization
- `l10n_py_account`: Accounting extensions
- `l10n_py_edi_base`: Electronic invoicing

Install those modules for complete functionality.

