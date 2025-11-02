# GUIA TÉCNICO DE IMPLEMENTAÇÃO
## Melhorias para Módulos de Localização Paraguaia

Este documento contém exemplos práticos de código para implementar as melhorias propostas nos módulos de localização paraguaia.

## 1. VALIDAÇÃO ROBUSTA DE RUC

### 1.1 Implementação do Validador de RUC

```python
# l10n_py_core/validators/ruc_validator.py
import re

from odoo.exceptions import ValidationError


class RUCValidator:
    """Validador robusto para RUC paraguaio"""

    # Multiplicadores para cálculo do dígito verificador
    MULTIPLIERS = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4]

    @classmethod
    def validate(cls, ruc):
        """
        Validação completa de RUC paraguaio

        Args:
            ruc (str): RUC a ser validado

        Returns:
            tuple: (is_valid, error_message)
        """
        if not ruc:
            return False, "RUC é obrigatório"

        # Limpar caracteres especiais
        clean_ruc = re.sub(r'[^\d-]', '', ruc)

        # Verificar formato básico
        if not re.match(r'^\d{6,8}-\d$', clean_ruc):
            return False, "Formato inválido. Use: XXXXXXX-D"

        # Separar RUC e dígito verificador
        ruc_number, check_digit = clean_ruc.split('-')

        # Validar comprimento
        if len(ruc_number) < 6 or len(ruc_number) > 8:
            return False, "RUC deve ter entre 6 e 8 dígitos"

        # Calcular dígito verificador
        calculated_digit = cls._calculate_check_digit(ruc_number)

        if str(calculated_digit) != check_digit:
            return False, "Dígito verificador inválido"

        return True, ""

    @classmethod
    def _calculate_check_digit(cls, ruc_number):
        """
        Calcular dígito verificador usando módulo 11

        Args:
            ruc_number (str): Número do RUC sem dígito verificador

        Returns:
            int: Dígito verificador calculado
        """
        # Ajustar comprimento para 8 dígitos (padding com zeros à esquerda)
        ruc_padded = ruc_number.zfill(8)

        # Calcular soma ponderada
        total = 0
        for i, digit in enumerate(ruc_padded):
            total += int(digit) * cls.MULTIPLIERS[i]

        # Calcular resto da divisão por 11
        remainder = total % 11

        # Determinar dígito verificador
        if remainder < 2:
            return remainder
        else:
            return 11 - remainder

    @classmethod
    def format_ruc(cls, ruc):
        """
        Formatar RUC para exibição padronizada

        Args:
            ruc (str): RUC a ser formatado

        Returns:
            str: RUC formatado
        """
        clean_ruc = re.sub(r'[^\d]', '', ruc)

        if len(clean_ruc) < 7:
            return ruc  # Retorna original se muito curto

        ruc_number = clean_ruc[:-1]
        check_digit = clean_ruc[-1]

        return f"{ruc_number}-{check_digit}"
```

### 1.2 Integração no Modelo res.partner

```python
# l10n_py_core/models/res_partner.py
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..validators.ruc_validator import RUCValidator


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_py_ruc = fields.Char(
        string='RUC',
        help='Registro Único de Contribuyentes',
        size=12
    )

    l10n_py_taxpayer_type = fields.Selection([
        ('1', 'Persona Física'),
        ('2', 'Persona Jurídica'),
        ('3', 'Extranjero'),
        ('4', 'Gobierno')
    ], string='Tipo de Contribuyente')

    l10n_py_ruc_formatted = fields.Char(
        string='RUC Formatado',
        compute='_compute_ruc_formatted',
        store=True
    )

    @api.depends('l10n_py_ruc')
    def _compute_ruc_formatted(self):
        """Computar RUC formatado"""
        for partner in self:
            if partner.l10n_py_ruc:
                partner.l10n_py_ruc_formatted = RUCValidator.format_ruc(
                    partner.l10n_py_ruc
                )
            else:
                partner.l10n_py_ruc_formatted = False

    @api.constrains('l10n_py_ruc')
    def _check_ruc(self):
        """Validar RUC"""
        for partner in self:
            if partner.l10n_py_ruc:
                is_valid, error = RUCValidator.validate(partner.l10n_py_ruc)
                if not is_valid:
                    raise ValidationError(
                        _('RUC inválido para %s: %s') % (partner.name, error)
                    )

    @api.onchange('l10n_py_ruc')
    def _onchange_ruc(self):
        """Formatar RUC automaticamente"""
        if self.l10n_py_ruc:
            self.l10n_py_ruc = RUCValidator.format_ruc(self.l10n_py_ruc)
```

## 2. GERAÇÃO ROBUSTA DE CDC

### 2.1 Gerador de CDC Conforme SIFEN

```python
import hashlib

# l10n_py_edi_core/services/cdc_generator.py
import random
from datetime import datetime

from odoo.exceptions import ValidationError


class CDCGenerator:
    """Gerador de Código de Control (CDC) para documentos eletrônicos"""

    # Multiplicadores para dígito verificador (posições 1-42)
    MULTIPLIERS = [2, 3, 4, 5, 6, 7, 8, 9] * 6  # Repetir até 42 posições

    @classmethod
    def generate(cls, company_ruc, doc_type, establishment,
                 expedition_point, sequence, emission_date=None):
        """
        Gerar CDC conforme especificação SIFEN v150

        Args:
            company_ruc (str): RUC da empresa emissora
            doc_type (int): Tipo de documento (1=FE, 4=Autofactura, etc.)
            establishment (str): Establecimiento (3 dígitos)
            expedition_point (str): Punto de expedición (3 dígitos)
            sequence (int): Número sequencial do documento
            emission_date (datetime): Data de emissão (opcional)

        Returns:
            str: CDC completo com dígito verificador
        """
        if emission_date is None:
            emission_date = datetime.now()

        # Extrair RUC sem dígito verificador (primeiros 8 dígitos)
        ruc_clean = ''.join(filter(str.isdigit, str(company_ruc)))
        ruc_number = ruc_clean[:8].zfill(8)

        # Construir CDC base (42 dígitos)
        cdc_base = cls._build_cdc_base(
            ruc_number, doc_type, establishment,
            expedition_point, sequence, emission_date
        )

        # Calcular dígito verificador
        check_digit = cls._calculate_check_digit(cdc_base)

        # CDC final (43 dígitos)
        cdc_complete = cdc_base + str(check_digit)

        # Validar formato final
        if len(cdc_complete) != 43:
            raise ValidationError(f"CDC deve ter 43 dígitos, gerado: {len(cdc_complete)}")

        return cdc_complete

    @classmethod
    def _build_cdc_base(cls, ruc_number, doc_type, establishment,
                        expedition_point, sequence, emission_date):
        """
        Construir base do CDC (42 dígitos)

        Formato conforme SIFEN:
        - RUC: 8 dígitos
        - Tipo documento: 2 dígitos
        - Establecimiento: 3 dígitos
        - Punto expedición: 3 dígitos
        - Número documento: 7 dígitos
        - Código segurança: 8 dígitos
        - Data/hora: 11 dígitos (YYMMDDHHmm + random)
        """
        # RUC da empresa (8 dígitos)
        cdc = ruc_number.zfill(8)

        # Tipo de documento (2 dígitos)
        cdc += f"{doc_type:02d}"

        # Establecimiento (3 dígitos)
        cdc += f"{int(establishment):03d}"

        # Punto de expedición (3 dígitos)
        cdc += f"{int(expedition_point):03d}"

        # Número do documento (7 dígitos)
        cdc += f"{sequence:07d}"

        # Código de segurança (8 dígitos) - gerado aleatoriamente
        security_code = cls._generate_security_code()
        cdc += f"{security_code:08d}"

        # Data e hora (11 dígitos)
        datetime_code = cls._generate_datetime_code(emission_date)
        cdc += datetime_code

        return cdc

    @classmethod
    def _generate_security_code(cls):
        """Gerar código de segurança aleatório (8 dígitos)"""
        return random.randint(10000000, 99999999)

    @classmethod
    def _generate_datetime_code(cls, emission_date):
        """
        Gerar código de data/hora (11 dígitos)

        Formato: YYMMDDHHmm + dígito aleatório
        """
        date_str = emission_date.strftime("%y%m%d%H%M")  # 10 dígitos
        random_digit = random.randint(0, 9)  # 1 dígito

        return date_str + str(random_digit)

    @classmethod
    def _calculate_check_digit(cls, cdc_base):
        """
        Calcular dígito verificador usando módulo 11

        Args:
            cdc_base (str): CDC base (42 dígitos)

        Returns:
            int: Dígito verificador (0-9)
        """
        if len(cdc_base) != 42:
            raise ValidationError(f"CDC base deve ter 42 dígitos, recebido: {len(cdc_base)}")

        # Calcular soma ponderada
        total = 0
        for i, digit in enumerate(cdc_base):
            multiplier = cls.MULTIPLIERS[i % len(cls.MULTIPLIERS)]
            total += int(digit) * multiplier

        # Calcular resto da divisão por 11
        remainder = total % 11

        # Determinar dígito verificador
        if remainder < 2:
            return remainder
        else:
            return 11 - remainder

    @classmethod
    def validate_cdc(cls, cdc):
        """
        Validar formato e dígito verificador de um CDC

        Args:
            cdc (str): CDC a ser validado

        Returns:
            tuple: (is_valid, error_message)
        """
        if not cdc:
            return False, "CDC é obrigatório"

        # Verificar comprimento
        if len(cdc) != 43:
            return False, f"CDC deve ter 43 dígitos, recebido: {len(cdc)}"

        # Verificar se contém apenas dígitos
        if not cdc.isdigit():
            return False, "CDC deve conter apenas números"

        # Separar base e dígito verificador
        cdc_base = cdc[:42]
        check_digit = int(cdc[42])

        # Calcular dígito verificador esperado
        calculated_digit = cls._calculate_check_digit(cdc_base)

        if calculated_digit != check_digit:
            return False, "Dígito verificador inválido"

        return True, ""
```

### 2.2 Integração no Modelo account.move

```python
# l10n_py_edi_core/models/account_move.py
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..services.cdc_generator import CDCGenerator


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_py_cdc = fields.Char(
        string='CDC',
        readonly=True,
        copy=False,
        help='Código de Control del documento electrónico'
    )

    l10n_py_edi_document_type = fields.Selection([
        ('1', 'Factura Electrónica'),
        ('4', 'Autofactura Electrónica'),
        ('5', 'Nota de Crédito Electrónica'),
        ('6', 'Nota de Débito Electrónica'),
        ('7', 'Nota de Remisión Electrónica'),
    ], string='Tipo Documento EDI', compute='_compute_edi_document_type')

    @api.depends('move_type', 'journal_id')
    def _compute_edi_document_type(self):
        """Determinar tipo de documento EDI baseado no tipo de movimento"""
        for move in self:
            if move.move_type == 'out_invoice':
                move.l10n_py_edi_document_type = '1'  # Factura Electrónica
            elif move.move_type == 'out_refund':
                move.l10n_py_edi_document_type = '5'  # Nota de Crédito
            elif move.move_type == 'in_invoice':
                move.l10n_py_edi_document_type = '4'  # Autofactura
            else:
                move.l10n_py_edi_document_type = False

    def _generate_cdc(self):
        """Gerar CDC para o documento"""
        self.ensure_one()

        if not self.company_id.l10n_py_ruc:
            raise ValidationError("Configure o RUC da empresa")

        if not self.journal_id.l10n_py_establishment:
            raise ValidationError("Configure o establecimiento no diário")

        if not self.journal_id.l10n_py_expedition_point:
            raise ValidationError("Configure o punto de expedición no diário")

        # Extrair número sequencial da fatura
        sequence_number = self._get_sequence_number()

        # Gerar CDC
        cdc = CDCGenerator.generate(
            company_ruc=self.company_id.l10n_py_ruc,
            doc_type=int(self.l10n_py_edi_document_type),
            establishment=self.journal_id.l10n_py_establishment,
            expedition_point=self.journal_id.l10n_py_expedition_point,
            sequence=sequence_number,
            emission_date=self.invoice_date or fields.Date.today()
        )

        self.l10n_py_cdc = cdc
        return cdc

    def _get_sequence_number(self):
        """Extrair número sequencial da fatura"""
        if not self.name:
            raise ValidationError("Documento deve ter um número")

        # Extrair apenas os dígitos do final do número
        import re
        numbers = re.findall(r'\d+', self.name)
        if not numbers:
            raise ValidationError(f"Não foi possível extrair número sequencial de: {self.name}")

        return int(numbers[-1])  # Último número encontrado
```

## 3. SISTEMA DE LOGS AVANÇADO

### 3.1 Modelo de Log EDI

```python
import json
import logging

# l10n_py_edi_core/models/edi_log.py
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class EDILog(models.Model):
    _name = 'l10n_py.edi.log'
    _description = 'Log de Operações EDI Paraguay'
    _order = 'create_date desc'
    _rec_name = 'operation_type'

    # Identificação da operação
    operation_type = fields.Selection([
        ('send', 'Envio de Documento'),
        ('status', 'Consulta de Status'),
        ('cancel', 'Cancelación'),
        ('event', 'Evento'),
        ('download', 'Download PDF/XML'),
        ('validate', 'Validação'),
    ], string='Tipo de Operação', required=True)

    # Documentos relacionados
    document_id = fields.Many2one(
        'account.move',
        string='Documento',
        ondelete='cascade'
    )

    cdc = fields.Char(string='CDC', index=True)

    # Provedor EDI
    provider = fields.Selection([
        ('factpy', 'FactPy'),
        ('facturasend', 'FacturaSend'),
        ('sifen', 'SIFEN Directo'),
        ('local', 'Processamento Local')
    ], string='Provedor', required=True)

    # Dados da requisição
    endpoint = fields.Char(string='Endpoint')
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE')
    ], string='Método HTTP')

    request_headers = fields.Text(string='Headers da Requisição')
    request_data = fields.Text(string='Dados Enviados')

    # Dados da resposta
    status_code = fields.Integer(string='Código de Status')
    response_headers = fields.Text(string='Headers da Resposta')
    response_data = fields.Text(string='Resposta Recebida')

    # Métricas
    execution_time = fields.Float(
        string='Tempo de Execução (ms)',
        help='Tempo de execução em milissegundos'
    )

    # Status e erro
    success = fields.Boolean(string='Sucesso', default=True)
    error_message = fields.Text(string='Mensagem de Erro')
    error_code = fields.Char(string='Código de Erro')

    # Dados adicionais
    batch_id = fields.Char(string='ID do Lote')
    retry_count = fields.Integer(string='Tentativas', default=0)

    @api.model
    def log_operation(self, operation_type, provider, document=None,
                     request_data=None, response_data=None,
                     execution_time=0, success=True,
                     error_message=None, **kwargs):
        """
        Registrar operação EDI

        Args:
            operation_type (str): Tipo de operação
            provider (str): Provedor EDI
            document (account.move): Documento relacionado
            request_data (dict): Dados da requisição
            response_data (dict): Dados da resposta
            execution_time (float): Tempo de execução em ms
            success (bool): Se a operação foi bem-sucedida
            error_message (str): Mensagem de erro (se houver)
            **kwargs: Campos adicionais
        """
        try:
            # Preparar dados do log
            log_vals = {
                'operation_type': operation_type,
                'provider': provider,
                'execution_time': execution_time,
                'success': success,
                'error_message': error_message,
            }

            # Documento relacionado
            if document:
                log_vals['document_id'] = document.id
                log_vals['cdc'] = document.l10n_py_cdc

            # Dados da requisição
            if request_data:
                log_vals['request_data'] = json.dumps(
                    request_data, indent=2, ensure_ascii=False
                )

            # Dados da resposta
            if response_data:
                log_vals['response_data'] = json.dumps(
                    response_data, indent=2, ensure_ascii=False
                )[:10000]  # Limitar tamanho

            # Campos adicionais
            for key, value in kwargs.items():
                if key in self._fields:
                    log_vals[key] = value

            # Criar registro de log
            return self.create(log_vals)

        except Exception as e:
            _logger.error(f"Erro ao criar log EDI: {str(e)}")
            return False

    def action_view_document(self):
        """Abrir documento relacionado"""
        self.ensure_one()
        if not self.document_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.document_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_retry_operation(self):
        """Repetir operação (se aplicável)"""
        self.ensure_one()

        if self.operation_type == 'send' and self.document_id:
            return self.document_id.action_send_edi()

        return False
```

### 3.2 Mixin para Logging Automático

```python
import logging
import time
from contextlib import contextmanager

# l10n_py_edi_core/models/edi_logging_mixin.py
from odoo import api, models

_logger = logging.getLogger(__name__)

class EDILoggingMixin(models.AbstractModel):
    _name = 'l10n_py.edi.logging.mixin'
    _description = 'Mixin para Logging Automático EDI'

    @contextmanager
    def log_edi_operation(self, operation_type, provider, document=None, **kwargs):
        """
        Context manager para logging automático de operações EDI

        Usage:
            with self.log_edi_operation('send', 'factpy', document):
                result = self.send_to_provider(data)
                yield result
        """
        start_time = time.time()
        log_data = {
            'operation_type': operation_type,
            'provider': provider,
            'document': document,
            **kwargs
        }

        try:
            yield log_data

            # Operação bem-sucedida
            execution_time = (time.time() - start_time) * 1000
            self.env['l10n_py.edi.log'].log_operation(
                execution_time=execution_time,
                success=True,
                **log_data
            )

        except Exception as e:
            # Operação com erro
            execution_time = (time.time() - start_time) * 1000
            self.env['l10n_py.edi.log'].log_operation(
                execution_time=execution_time,
                success=False,
                error_message=str(e),
                **log_data
            )
            raise
```

## 4. CONECTOR OTIMIZADO PARA FACTURASEND

### 4.1 Cliente HTTP Robusto

```python
import json
import logging
import time

# l10n_py_edi_facturasend/services/facturasend_client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class FacturaSendClient:
    """Cliente HTTP robusto para FacturaSend"""

    def __init__(self, api_key, tenant_id, environment='test', timeout=30):
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.environment = environment
        self.timeout = timeout

        # URLs base por ambiente
        self.base_urls = {
            'test': 'https://api-test.facturasend.com.py',
            'prod': 'https://api.facturasend.com.py'
        }

        # Configurar sessão com retry automático
        self.session = self._setup_session()

    def _setup_session(self):
        """Configurar sessão HTTP com retry e timeouts"""
        session = requests.Session()

        # Configurar estratégia de retry
        retry_strategy = Retry(
            total=3,  # Máximo 3 tentativas
            backoff_factor=1,  # Intervalo entre tentativas
            status_forcelist=[429, 500, 502, 503, 504],  # Status codes para retry
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
        )

        # Aplicar adapter com retry
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self):
        """Obter headers padrão para requisições"""
        return {
            'Authorization': f'Bearer api_key_{self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Odoo-L10n-PY/1.0'
        }

    def _get_url(self, endpoint):
        """Construir URL completa"""
        base_url = self.base_urls[self.environment]
        return f"{base_url}/{self.tenant_id}/{endpoint.lstrip('/')}"

    def _make_request(self, method, endpoint, data=None, params=None):
        """
        Fazer requisição HTTP com logging e tratamento de erros

        Args:
            method (str): Método HTTP (GET, POST, etc.)
            endpoint (str): Endpoint da API
            data (dict): Dados para envio (JSON)
            params (dict): Parâmetros da query string

        Returns:
            dict: Resposta da API
        """
        url = self._get_url(endpoint)
        headers = self._get_headers()

        # Log da requisição
        _logger.info(f"FacturaSend API: {method} {url}")
        if data:
            _logger.debug(f"Request data: {json.dumps(data, indent=2)}")

        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.timeout
            )

            execution_time = (time.time() - start_time) * 1000

            # Log da resposta
            _logger.info(f"FacturaSend API Response: {response.status_code} "
                        f"({execution_time:.2f}ms)")

            # Processar resposta
            return self._process_response(response)

        except requests.exceptions.Timeout:
            raise UserError("Timeout: FacturaSend não respondeu a tempo")
        except requests.exceptions.ConnectionError:
            raise UserError("Erro de conexão com FacturaSend")
        except Exception as e:
            _logger.exception("Erro na requisição FacturaSend")
            raise UserError(f"Erro inesperado: {str(e)}")

    def _process_response(self, response):
        """
        Processar resposta da API

        Args:
            response (requests.Response): Resposta HTTP

        Returns:
            dict: Dados da resposta processados
        """
        try:
            data = response.json()
        except ValueError:
            data = {'raw_response': response.text}

        if response.status_code == 200:
            return {
                'success': True,
                'data': data,
                'status_code': response.status_code
            }
        elif response.status_code == 401:
            raise UserError("Credenciais inválidas. Verifique API Key e Tenant ID")
        elif response.status_code == 403:
            raise UserError("Acesso negado. Verifique permissões da API Key")
        elif response.status_code == 429:
            raise UserError("Limite de requisições excedido. Tente novamente mais tarde")
        else:
            error_msg = data.get('message', response.text) if data else response.text
            raise UserError(f"Erro FacturaSend ({response.status_code}): {error_msg}")

    # Métodos específicos da API FacturaSend

    def send_document(self, document_data):
        """Enviar documento para FacturaSend"""
        return self._make_request('POST', 'lote/create', data=[document_data])

    def check_status(self, batch_id):
        """Consultar status de um lote"""
        return self._make_request('GET', f'lote/{batch_id}/status')

    def download_pdf(self, cdc):
        """Download do PDF (KUDE)"""
        return self._make_request('GET', f'documento/{cdc}/pdf')

    def download_xml(self, cdc):
        """Download do XML assinado"""
        return self._make_request('GET', f'documento/{cdc}/xml')

    def cancel_document(self, cdc, reason):
        """Cancelar documento"""
        data = {'motivo': reason}
        return self._make_request('POST', f'documento/{cdc}/cancelar', data=data)

    def test_connection(self):
        """Testar conectividade"""
        try:
            return self._make_request('GET', 'status')
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

Este guia técnico fornece implementações práticas e robustas para as principais melhorias propostas. Cada seção inclui código funcional que pode ser diretamente implementado nos módulos de localização paraguaia.

As implementações seguem as melhores práticas do Odoo e estão alinhadas com os requisitos do SIFEN conforme o manual técnico v150.
