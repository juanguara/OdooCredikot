# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrmSoapLog(models.Model):
    _name = "crm.soap.log"
    _description = "CRM SOAP Hook Log"
    _order = "id desc"

    name = fields.Char(string="Logger", default="crm_soap_state_hook", index=True)
    level = fields.Selection([
        ("DEBUG", "DEBUG"),
        ("INFO", "INFO"),
        ("WARNING", "WARNING"),
        ("ERROR", "ERROR"),
    ], default="INFO", index=True)
    message = fields.Text(string="Message")
    payload = fields.Text(string="Payload (XML)")
    response = fields.Text(string="Response Body")
    url = fields.Char(string="URL")
    status_code = fields.Integer(string="HTTP Status")
    usucod = fields.Char(string="Usucod")
    riepedid = fields.Char(string="Riepedid")
    riepedinfrespcod = fields.Char(string="Riepedinfrespcod_nuevo")
    is_won = fields.Boolean(string="Is Won?")
    logica_cambio = fields.Char(string="LogicaCambioEstado")
    create_date = fields.Datetime(string="Created", readonly=True)
