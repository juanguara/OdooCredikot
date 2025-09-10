# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

PARAM_PREFIX = 'crm_soap_state_hook.'

def _p(name: str) -> str:
    return f"{PARAM_PREFIX}{name}"

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # --- Activación y stage perdido ---
    crm_soap_enable = fields.Boolean(string="Habilitar SOAP Hook")
    crm_lost_stage_id = fields.Many2one(
        'crm.stage',
        string="Etapa de PERDIDO (detona hook al marcar Perdida)",
        help="Etapa que Odoo considera como 'perdida'. Se utiliza por si verificás estados manualmente."
    )

    # --- Conexión SOAP / Credenciales ---
    crm_soap_url = fields.Char(string="URL SOAP",
                               help="Ej: http://IP:PUERTO/aRiesgoSeguimientoMsgAdd_2_WS.aspx")
    crm_soap_timeout = fields.Integer(string="Timeout (segundos)", default=15)
    crm_soap_usucod = fields.Char(string="Usucod (Legacy)", help="Código de usuario Legacy para el servicio.")

    # --- Parámetro exigido por WSDL (X/U/M) ---
    crm_soap_logica_cambio = fields.Selection(
        selection=[('X', 'X'), ('U', 'U'), ('M', 'M')],
        string="LogicaCambioEstado",
        default='U',
        help="Valor requerido por el WSDL: X, U o M. Por defecto U."
    )

    # --- Valores de negocio por resultado ---
    crm_soap_riepedinfrespcod_won = fields.Char(
        string="Riepedinfrespcod (GANADO)", help="Ej: OP-A-LIQ"
    )
    crm_soap_riepedinfrespcod_lost = fields.Char(
        string="Riepedinfrespcod (PERDIDO)", help="Ej: DE"
    )
    crm_soap_msg_won = fields.Char(string="Mensaje (GANADO)", default="Oportunidad Ganada")
    crm_soap_msg_lost = fields.Char(string="Mensaje (PERDIDO)", default="Oportunidad Perdida")

    # --- Logging a archivo/terminal ---
    crm_soap_log_enable = fields.Boolean(string="Log a sistema", default=True)
    crm_soap_log_payload = fields.Boolean(string="Log de Payload SOAP", default=True)
    crm_soap_log_response = fields.Boolean(string="Log de Respuesta SOAP", default=True)
    crm_soap_log_snippet_len = fields.Integer(string="Longitud snippet", default=600)
    crm_soap_log_mask_usucod = fields.Boolean(string="Enmascarar Usucod en logs", default=True)

    # --- Logging a base de datos (ir.logging) ---
    crm_soap_log_db_enable = fields.Boolean(string="Log a Base de Datos", default=True)
    crm_soap_log_db_payload = fields.Boolean(string="Log Payload a BD", default=True)
    crm_soap_log_db_response = fields.Boolean(string="Log Respuesta a BD", default=True)

    # -------------------------------------------------------------------------
    # Helpers de conversión
    # -------------------------------------------------------------------------
    def _get_bool(self, icp, key, default=False):
        val = icp.get_param(key, default=str(bool(default)))
        # Aceptamos varias convenciones
        return str(val).strip() in ('True', 'true', '1', 'yes', 'y', 'on')

    def _get_int(self, icp, key, default=0):
        try:
            return int(icp.get_param(key, default=str(int(default))) or default)
        except Exception:
            return default

    # -------------------------------------------------------------------------
    # Load/Save hacia ir.config_parameter
    # -------------------------------------------------------------------------
    @api.model
    def get_values(self):
        res = super().get_values()
        icp = self.env['ir.config_parameter'].sudo()

        # Lectura
        res.update({
            'crm_soap_enable': self._get_bool(icp, _p('enable'), True),
            'crm_soap_url': icp.get_param(_p('url'), default="http://119.8.77.187:8080/aRiesgoSeguimientoMsgAdd_2_WS.aspx"),
            'crm_soap_timeout': self._get_int(icp, _p('timeout'), 15),
            'crm_soap_usucod': icp.get_param(_p('usucod'), default="38"),
            'crm_soap_logica_cambio': icp.get_param(_p('logica_cambio'), default="U"),

            'crm_soap_riepedinfrespcod_won': icp.get_param(_p('riepedinfrespcod_won'), default="OP-A-LIQ"),
            'crm_soap_riepedinfrespcod_lost': icp.get_param(_p('riepedinfrespcod_lost'), default="DE"),
            'crm_soap_msg_won': icp.get_param(_p('msg_won'), default="Oportunidad Ganada"),
            'crm_soap_msg_lost': icp.get_param(_p('msg_lost'), default="Oportunidad Perdida"),

            'crm_soap_log_enable': self._get_bool(icp, _p('log.enable'), True),
            'crm_soap_log_payload': self._get_bool(icp, _p('log.payload'), True),
            'crm_soap_log_response': self._get_bool(icp, _p('log.response'), True),
            'crm_soap_log_snippet_len': self._get_int(icp, _p('log.snippet_len'), 600),
            'crm_soap_log_mask_usucod': self._get_bool(icp, _p('log.mask_usucod'), True),

            'crm_soap_log_db_enable': self._get_bool(icp, _p('log.db.enable'), True),
            'crm_soap_log_db_payload': self._get_bool(icp, _p('log.db.payload'), True),
            'crm_soap_log_db_response': self._get_bool(icp, _p('log.db.response'), True),
        })

        # Many2one: guardamos/recuperamos id como entero
        lost_stage_id = self._get_int(icp, _p('lost_stage_id'), 0)
        if lost_stage_id:
            res['crm_lost_stage_id'] = lost_stage_id
        else:
            res['crm_lost_stage_id'] = False

        return res

    def set_values(self):
        super().set_values()
        icp = self.env['ir.config_parameter'].sudo()

        # Escritura (cast a str siempre)
        icp.set_param(_p('enable'), str(bool(self.crm_soap_enable)))
        icp.set_param(_p('url'), self.crm_soap_url or "")
        icp.set_param(_p('timeout'), str(int(self.crm_soap_timeout or 15)))
        icp.set_param(_p('usucod'), self.crm_soap_usucod or "")
        icp.set_param(_p('logica_cambio'), self.crm_soap_logica_cambio or "U")

        icp.set_param(_p('riepedinfrespcod_won'), self.crm_soap_riepedinfrespcod_won or "")
        icp.set_param(_p('riepedinfrespcod_lost'), self.crm_soap_riepedinfrespcod_lost or "")
        icp.set_param(_p('msg_won'), self.crm_soap_msg_won or "")
        icp.set_param(_p('msg_lost'), self.crm_soap_msg_lost or "")

        icp.set_param(_p('log.enable'), str(bool(self.crm_soap_log_enable)))
        icp.set_param(_p('log.payload'), str(bool(self.crm_soap_log_payload)))
        icp.set_param(_p('log.response'), str(bool(self.crm_soap_log_response)))
        icp.set_param(_p('log.snippet_len'), str(int(self.crm_soap_log_snippet_len or 600)))
        icp.set_param(_p('log.mask_usucod'), str(bool(self.crm_soap_log_mask_usucod)))

        icp.set_param(_p('log.db.enable'), str(bool(self.crm_soap_log_db_enable)))
        icp.set_param(_p('log.db.payload'), str(bool(self.crm_soap_log_db_payload)))
        icp.set_param(_p('log.db.response'), str(bool(self.crm_soap_log_db_response)))

        # Many2one: persistimos id
        icp.set_param(_p('lost_stage_id'), str(int(self.crm_lost_stage_id.id)) if self.crm_lost_stage_id else "")
