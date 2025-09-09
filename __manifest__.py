# -*- coding: utf-8 -*-
{
    "name": "CRM SOAP State Hook",
    "summary": "Envia cambios de estado (Won/Lost) por SOAP al Legacy y agrega logs",
    "version": "18.0.1.0",
    "author": "Tu Equipo",
    "website": "",
    "category": "CRM",
    "license": "LGPL-3",
    "depends": ["base", "crm"],
    "data": [
        "views/res_config_settings_views.xml",   # <— Bloque en Ajustes
        "views/logging_menu.xml",                # <— Menú Logs (SOAP Hook) en Ajustes
    ],
    "installable": True,
    "application": False,
}