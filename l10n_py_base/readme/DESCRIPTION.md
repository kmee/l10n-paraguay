# Paraguay - Base Localization

This module provides the fundamental localization data for Paraguay in Odoo.

## Features

- **RUC Management**: Registro Único del Contribuyente (RUC) fields and validation
- **Document Types**: Support for Paraguayan identification documents
  - Cédula de Identidad
  - Passport
  - RUC
- **Taxpayer Types**: 
  - Contribuyente (taxpayer)
  - No Contribuyente (non-taxpayer)
- **Location Data**: Complete geographical structure
  - Departments (departamentos)
  - Districts (distritos)
  - Cities (ciudades)
- **Fiscal Validation**: Validation methods for fiscal data
- **Partner Extensions**: Enhanced partner model with Paraguayan fiscal requirements

## Purpose

This is a foundational module required by all other Paraguayan localization modules. It extends the partner model with essential fiscal data fields needed for compliance with Paraguayan tax regulations.

## Dependencies

- `base`: Odoo core module
- `base_address_extended`: Extended address functionality

