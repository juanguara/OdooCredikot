# placeholder res_config_settings
# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Habilitar/Deshabilitar integración
    crm_soap_enable = fields.Boolean(
        string="Habilitar SOAP (Won/Lost)",
        config_parameter="crm_soap_state_hook.enable",
        default=True,
    )

    # Parámetros SOAP
    crm_soap_url = fields.Char(
        string="URL SOAP",
        config_parameter="crm_soap_state_hook.url",
        default="http://119.8.77.187:8080/aRiesgoSeguimientoMsgAdd_2_WS.aspx",
    )
    crm_soap_timeout = fields.Integer(
        string="Timeout (s)",
        config_parameter="crm_soap_state_hook.timeout",
        default=15,
    )
    crm_soap_usucod = fields.Char(
        string="Usucod",
        config_parameter="crm_soap_state_hook.usucod",
        default="38",
    )
    crm_soap_riepedinfrespcod_won = fields.Char(
        string="Cód. Respuesta (Won)",
        config_parameter="crm_soap_state_hook.riepedinfrespcod_won",
        default="OP-A-LIQ",
    )
    crm_soap_riepedinfrespcod_lost = fields.Char(
        string="Cód. Respuesta (Lost)",
        config_parameter="crm_soap_state_hook.riepedinfrespcod_lost",
        default="DE",
    )
    crm_soap_msg_won = fields.Char(
        string="Mensaje (Won)",
        config_parameter="crm_soap_state_hook.msg_won",
        default="Oportunidad Ganada",
    )
    crm_soap_msg_lost = fields.Char(
        string="Mensaje (Lost)",
        config_parameter="crm_soap_state_hook.msg_lost",
        default="Oportunidad Perdida",
    )

    # (Opcional) Etapa considerada Lost (para atajos o validaciones)
    crm_lost_stage_id = fields.Many2one(
        "crm.stage",
        string="Etapa Perdida (opcional)",
        config_parameter="crm_soap_state_hook.lost_stage_id",
    )

    # Flags de logging a fichero
    crm_soap_log_enable = fields.Boolean(
        string="Log en fichero",
        config_parameter="crm_soap_state_hook.log.enable",
        default=True,
    )
    crm_soap_log_payload = fields.Boolean(
        string="Incluir Payload en log",
        config_parameter="crm_soap_state_hook.log.payload",
        default=True,
    )
    crm_soap_log_response = fields.Boolean(
        string="Incluir Respuesta en log",
        config_parameter="crm_soap_state_hook.log.response",
        default=True,
    )
    crm_soap_log_snippet_len = fields.Integer(
        string="Tamaño snippet",
        config_parameter="crm_soap_state_hook.log.snippet_len",
        default=600,
    )
    crm_soap_log_mask_usucod = fields.Boolean(
        string="Enmascarar Usucod en log",
        config_parameter="crm_soap_state_hook.log.mask_usucod",
        default=True,
    )

    # Logging a Base de Datos (menú Logs (SOAP Hook))
    crm_soap_log_db_enable = fields.Boolean(
        string="Log en Base de Datos",
        config_parameter="crm_soap_state_hook.log.db.enable",
        default=True,
    )
    crm_soap_log_db_payload = fields.Boolean(
        string="Guardar Payload (DB)",
        config_parameter="crm_soap_state_hook.log.db.payload",
        default=True,
    )
    crm_soap_log_db_response = fields.Boolean(
        string="Guardar Respuesta (DB)",
        config_parameter="crm_soap_state_hook.log.db.response",
        default=True,
    )
