# -*- coding: utf-8 -*-
import logging
import html
import requests

from odoo import models, _, api

_logger = logging.getLogger("odoo.addons.crm_soap_state_hook.models.crm_lead")

class CrmLead(models.Model):
    _inherit = "crm.lead"

    # ---------- Helpers: Config & Logging ----------
    def _get_hook_config(self):
        ICP = self.env["ir.config_parameter"].sudo()
        def _b(k, d="True"):
            return str(ICP.get_param(k, d)).strip().lower() in ("1","true","t","yes","y","si","sí")
        def _i(k, d="15"):
            try:
                return int(ICP.get_param(k, d) or d)
            except Exception:
                return int(d)
        get = lambda k, d="": (ICP.get_param(k, d) or d)

        return {
            "enable": _b("crm_soap_state_hook.enable", "True"),
            "url": get("crm_soap_state_hook.url", ""),
            "timeout": _i("crm_soap_state_hook.timeout", "15"),
            "usucod": get("crm_soap_state_hook.usucod", ""),
            "won_code": get("crm_soap_state_hook.riepedinfrespcod_won", "OP-A-LIQ"),
            "lost_code": get("crm_soap_state_hook.riepedinfrespcod_lost", "DE"),
            "msg_won": get("crm_soap_state_hook.msg_won", "Oportunidad Ganada"),
            "msg_lost": get("crm_soap_state_hook.msg_lost", "Oportunidad Perdida"),
            "log": _b("crm_soap_state_hook.log.enable", "True"),
            "log_payload": _b("crm_soap_state_hook.log.payload", "True"),
            "log_response": _b("crm_soap_state_hook.log.response", "True"),
            "log_mask": _b("crm_soap_state_hook.log.mask_usucod", "True"),
            "log_db": _b("crm_soap_state_hook.log.db.enable", "True"),
            "log_db_payload": _b("crm_soap_state_hook.log.db.payload", "True"),
            "log_db_response": _b("crm_soap_state_hook.log.db.response", "True"),
            "lost_stage_id": get("crm_soap_state_hook.lost_stage_id", ""),
            "soapaction": get("crm_soap_state_hook.soapaction", "GX#RiesgoSeguimientoMsgAdd_2_WS.Execute"),
            "logica": get("crm_soap_state_hook.logica_cambio_estado", "U"),
        }

    def _log_file(self, level, msg, **kwargs):
        if kwargs:
            msg = f"{msg} | {kwargs}"
        getattr(_logger, level.lower(), _logger.info)(msg)

    def _log_db(self, level, message, **vals):
        ICP = self.env["ir.config_parameter"].sudo()
        if str(ICP.get_param("crm_soap_state_hook.log.db.enable", "True")).strip().lower() not in ("1","true","t","yes","y","si","sí"):
            return
        Log = self.env["crm.soap.log"].sudo()
        Log.create({
            "level": level,
            "message": message,
            **vals,
        })

    # ---------- SOAP helpers ----------
    def _soap_build_envelope(self, usucod, riepedid, riepedinfrespcod, mensaje, logica):
        esc = lambda x: html.escape(str(x or ""), quote=True)
        # Incluimos LogicaCambioEstado como nos respondió el servicio (X/U/M), default 'U'
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="GX">
  <SOAP-ENV:Body>
    <ns1:RiesgoSeguimientoMsgAdd_2_WS.Execute>
      <ns1:Usucod>{esc(usucod)}</ns1:Usucod>
      <ns1:Riepedid>{esc(riepedid)}</ns1:Riepedid>
      <ns1:Riepedinfrespcod_nuevo>{esc(riepedinfrespcod)}</ns1:Riepedinfrespcod_nuevo>
      <ns1:Riepedsegrmensaje>{esc(mensaje)}</ns1:Riepedsegrmensaje>
      <ns1:LogicaCambioEstado>{esc(logica)}</ns1:LogicaCambioEstado>
    </ns1:RiesgoSeguimientoMsgAdd_2_WS.Execute>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        return xml.encode("utf-8")

    def _soap_post(self, url, payload, timeout, soapaction, usucod, cfg):
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": soapaction or "GX#RiesgoSeguimientoMsgAdd_2_WS.Execute",
            "User-Agent": "Odoo/18 CRM SOAP Hook",
        }
        # Logs (file)
        if cfg.get("log"):
            self._log_file("info", "SOAP request: POST", url=url, timeout=timeout, payload_len=len(payload))
            if cfg.get("log_payload"):
                self._log_file("debug", "SOAP payload", snippet=payload.decode("utf-8", errors="ignore")[:800])

        # DB Log (pre)
        db_vals = {
            "url": url,
            "payload": payload.decode("utf-8", errors="ignore") if cfg.get("log_db_payload") else False,
            "usucod": "***" if cfg.get("log_mask") else (usucod or ""),
        }

        resp = requests.post(url, data=payload, headers=headers, timeout=timeout)
        status = resp.status_code
        text = resp.text or ""
        # Logs
        if cfg.get("log"):
            self._log_file("info", "SOAP response", status=status, body_len=len(text))
            if cfg.get("log_response"):
                self._log_file("debug", "SOAP response body", snippet=text[:800])

        # DB log (post)
        db_vals.update({
            "status_code": status,
            "response": text if cfg.get("log_db_response") else False,
        })
        self._log_db("INFO" if status == 200 else "ERROR", "SOAP call completed", **db_vals)

        if status != 200:
            raise models.UserError(_("Fallo SOAP (HTTP %s): %s") % (status, text[:800]))
        low = text.lower()
        if "<fault>" in low or "<soap:fault" in low or "<soap-env:fault" in low:
            raise models.UserError(_("El servicio SOAP devolvió Fault: %s") % (text[:800]))
        # Extraer MsgErr (por si lo hay)
        me = self._soap_extract_msgerr(text)
        if me:
            # Lo registramos pero no cortamos, salvo que quieras levantar error
            self._log_db("WARNING", f"SOAP MsgErr: {me}", **db_vals)
        return text

    def _soap_extract_msgerr(self, body):
        # Busca MsgErr en variantes
        low = body.lower()
        tags = ["<msgerr>", "<ns1:msgerr>", "<MSGERR>".lower(), "<ns1:MSGERR>".lower()]
        for t in tags:
            i = low.find(t.lower())
            if i >= 0:
                close = "</" + t.strip("<>").split(":")[-1] + ">"
                j = low.find(close.lower(), i + len(t))
                if j > i:
                    return body[i+len(t):j].strip()
        return ""

    # ---------- Public API ----------
    def _call_legacy_state_change(self, mensaje, is_won):
        cfg = self._get_hook_config()
        if not cfg.get("enable"):
            return True
        url = (cfg.get("url") or "").strip()
        if not url:
            raise models.UserError(_("No está configurada la URL SOAP."))
        usucod = (cfg.get("usucod") or "").strip()
        timeout = cfg.get("timeout") or 15
        code = (cfg.get("won_code") if is_won else cfg.get("lost_code")) or ""
        logica = (cfg.get("logica") or "U").strip() or "U"

        # Log de inicio
        self._log_file("info", "SOAP change start", leads=len(self), is_won=is_won, url=url, timeout=timeout)
        self._log_db("INFO", "SOAP change start",
                     url=url, usucod="***" if cfg.get("log_mask") else usucod, is_won=is_won,
                     riepedinfrespcod=code, logica_cambio=logica)

        for lead in self.sudo():
            riepedid = getattr(lead, "x_studio_solicitud", None)
            if not riepedid:
                raise models.UserError(_("La oportunidad %s no tiene x_studio_solicitud (requerido para Riepedid).") % (lead.display_name))

            payload = self._soap_build_envelope(usucod, riepedid, code, mensaje, logica)
            text = self._soap_post(url, payload, timeout, cfg.get("soapaction"), usucod, cfg)

            # DB log por lead
            self._log_db("INFO", "SOAP OK por lead",
                         url=url, usucod="***" if cfg.get("log_mask") else usucod,
                         riepedid=str(riepedid), riepedinfrespcod=code, is_won=is_won)

        return True

    def _move_to_lost_stage(self):
        cfg = self._get_hook_config()
        sid = 0
        try:
            sid = int(cfg.get("lost_stage_id") or 0)
        except Exception:
            sid = 0
        if not sid:
            return
        Stage = self.env["crm.stage"].sudo()
        target = Stage.browse(sid).exists()
        for lead in self.sudo():
            st = target
            if target and target.team_id and lead.team_id and target.team_id != lead.team_id:
                alt = Stage.search([("name","=", target.name), "|", ("team_id","=", lead.team_id.id), ("team_id","=", False)], limit=1)
                st = alt or target
            if st:
                lead.with_context(tracking_disable=True, mail_notrack=True).write({"stage_id": st.id})

    # ---------- Overrides ----------
    def action_set_won(self):
        res = super().action_set_won()
        msg = self._get_hook_config().get("msg_won") or "Oportunidad Ganada"
        self._call_legacy_state_change(msg, is_won=True)
        return res

    def _action_set_lost(self, **additional_values):
        res = super()._action_set_lost(**additional_values)
        msg = self._get_hook_config().get("msg_lost") or "Oportunidad Perdida"
        self._call_legacy_state_change(msg, is_won=False)
        self._move_to_lost_stage()
        return res

    def action_set_lost(self, **kwargs):
        res = super().action_set_lost(**kwargs)
        msg = self._get_hook_config().get("msg_lost") or "Oportunidad Perdida"
        self._call_legacy_state_change(msg, is_won=False)
        self._move_to_lost_stage()
        return res
