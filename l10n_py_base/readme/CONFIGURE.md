# Configuration

## Company Setup

Configure your company's Paraguayan fiscal information:

1. Navigate to **Settings > General Settings > Companies**
2. Edit your company
3. In the **Fiscal Information** section:
   - Enter your **RUC** (format: XXXXXXXX-D)
   - Select **Taxpayer Type**
   - Choose **Department**, **District**, and **City**

## Partner Configuration

For each customer and vendor:

1. Go to **Contacts**
2. Create or edit a contact
3. Configure fiscal information:
   - **Document Type**: Select appropriate type (Cédula, Passport, RUC)
   - **Document Number**: Enter the identification number
   - **RUC**: If applicable
   - **Taxpayer Type**: Select Contribuyente or No Contribuyente
   - **Address**: Complete with Department, District, City

## RUC Validation

The system automatically validates RUC format:
- Must be 8 digits + verification digit
- Verification digit is calculated using module 11 algorithm
- Invalid RUC will trigger a warning

### Manual RUC Validation

If you need to validate a RUC:
1. The system performs automatic validation on save
2. Check for validation messages
3. Correct format: 12345678-9 (example)

## Location Data

The module includes pre-loaded data for:
- All 17 Paraguayan departments
- Districts within each department
- Major cities

### Adding Custom Locations

If needed, add custom cities/districts:
1. Go to **Settings > Technical > Localizations > Cities**
2. Create new city record
3. Link to appropriate district and state

## Address Configuration

Use the extended address fields:
1. **Street**: Street name and number
2. **Street2**: Additional address line
3. **Department**: Select from list
4. **District**: Auto-filtered by department
5. **City**: Auto-filtered by district
6. **ZIP**: Postal code

