# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestEDIValidation(TransactionCase):

    def setUp(self):
        super(TestEDIValidation, self).setUp()

        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company EDI',
            'country_id': self.env.ref('base.py').id,
            'l10n_py_ruc': '80009401-6',  # Valid RUC
        })

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'is_company': True,
            'country_id': self.env.ref('base.py').id,
            'l10n_py_ruc': '80009401-6',
            'l10n_py_taxpayer_type': '1',  # Contribuyente
            'street': 'Test Street 123',
        })

        # Create test journal
        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'type': 'sale',
            'code': 'TEST',
            'company_id': self.company.id,
            'l10n_py_establishment': '001',
            'l10n_py_point': '001',
            'l10n_py_timbrado': '12345678',
            'currency_id': self.env.ref('base.PYG').id,
        })

        # Create test product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'default_code': 'TEST001',
            'l10n_py_ncm_code': '01012100',  # Valid NCM
        })

    def test_ruc_validation(self):
        """Test RUC validation"""
        # Valid RUC
        self.assertTrue(self.partner._validate_ruc_format('80009401-6'))

        # Invalid RUC - wrong format
        self.assertFalse(self.partner._validate_ruc_format('800094016'))

        # Invalid RUC - too short
        self.assertFalse(self.partner._validate_ruc_format('800094-6'))

    def test_partner_fiscal_validation(self):
        """Test partner fiscal data validation"""
        # Valid partner should pass
        try:
            self.partner.validate_fiscal_data()
        except ValidationError:
            self.fail("Valid partner failed fiscal validation")

        # Invalid partner - missing RUC for taxpayer
        invalid_partner = self.env['res.partner'].create({
            'name': 'Invalid Partner',
            'is_company': True,
            'l10n_py_taxpayer_type': '1',  # Contribuyente without RUC
            'street': 'Test Street 123',
        })

        with self.assertRaises(ValidationError):
            invalid_partner.validate_fiscal_data()

    def test_invoice_edi_validation(self):
        """Test invoice EDI data validation"""
        # Create test invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'company_id': self.company.id,
            'invoice_date': '2024-01-01',
            'currency_id': self.env.ref('base.PYG').id,
            'l10n_py_emission_type': '1',
            'l10n_py_transaction_type': '1',
        })

        # Add invoice line
        self.env['account.move.line'].create({
            'move_id': invoice.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100000,
            'tax_ids': [(6, 0, [self.env.ref('l10n_py.iva_10').id])],
        })

        # Valid invoice should pass validation
        try:
            invoice._validate_edi_data()
        except ValidationError:
            self.fail("Valid invoice failed EDI validation")

    def test_security_code_generation(self):
        """Test security code generation"""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'company_id': self.company.id,
        })

        security_code = invoice._generate_security_code()

        # Should be 9 digits
        self.assertEqual(len(security_code), 9)
        self.assertTrue(security_code.isdigit())

    def test_document_type_computation(self):
        """Test document type computation"""
        # Invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'company_id': self.company.id,
        })
        self.assertEqual(invoice.l10n_py_edi_document_type, '1')

        # Credit note
        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'company_id': self.company.id,
        })
        self.assertEqual(credit_note.l10n_py_edi_document_type, '5')
