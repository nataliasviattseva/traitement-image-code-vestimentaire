import logging
import smtplib
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)




@dataclass
class EmailConfig:
    sender: str                    
    password: str                 
    recipients: list[str]          # destinataires
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587           # STARTTLS
    enabled: bool = True


@dataclass
class DressCodeAlert:
    filename: str
    reason: str                    
    confidence: float              
    timestamp: datetime = field(default_factory=datetime.now)
    location: Optional[str] = None
    detections: list[dict] = field(default_factory=list)

    # Labels humains
    REASON_LABELS = {
        "accessoire_interdit": "Accessoire interdit (casquette, bonnet…)",
        "vetement_interdit":   "Vêtement non conforme (crop top, short…)",
        "chaussure_interdite": "Chaussure interdite (tongs…)",
        "no_helmet":           "Équipement de sécurité manquant",
    }

    @property
    def reason_label(self) -> str:
        return self.REASON_LABELS.get(self.reason, self.reason)

    @property
    def confidence_pct(self) -> str:
        return f"{self.confidence * 100:.1f}%"

    @property
    def timestamp_str(self) -> str:
        return self.timestamp.strftime("%d/%m/%Y à %H:%M:%S")


# ---------------------------------------------------------------------------
# Rendu HTML de l'email
# ---------------------------------------------------------------------------

def _render_email_html(alert: DressCodeAlert) -> str:
    detections_rows = ""
    for d in alert.detections:
        label = d.get("label", "—")
        conf  = d.get("confidence", 0)
        detections_rows += f"""
        <tr>
          <td style="padding:6px 12px;border-bottom:1px solid #eee;">{label}</td>
          <td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right;">
            {conf * 100:.1f}%
          </td>
        </tr>"""

    location_row = (
        f'<p style="margin:4px 0;color:#555;">📍 Localisation : <strong>{alert.location}</strong></p>'
        if alert.location else ""
    )

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px;">
  <div style="max-width:560px;margin:auto;background:#fff;border-radius:8px;
              box-shadow:0 2px 8px rgba(0,0,0,.1);overflow:hidden;">

    <!-- Header -->
    <div style="background:#c0392b;padding:24px 28px;">
      <h1 style="color:#fff;margin:0;font-size:20px;">
        🚨 Alerte — Code Vestimentaire Non Respecté
      </h1>
      <p style="color:#f5b7b1;margin:6px 0 0;">ENSITECH · Système de surveillance automatique</p>
    </div>

    <!-- Body -->
    <div style="padding:24px 28px;">
      <p style="color:#222;font-size:15px;margin-top:0;">
        Une infraction au code vestimentaire a été détectée automatiquement.
      </p>

      <!-- Infraction -->
      <div style="background:#fdf2f2;border-left:4px solid #c0392b;
                  padding:14px 18px;border-radius:4px;margin-bottom:20px;">
        <p style="margin:4px 0;color:#555;">⚠️ Type d'infraction :</p>
        <p style="margin:4px 0;font-size:16px;font-weight:bold;color:#c0392b;">
          {alert.reason_label}
        </p>
        <p style="margin:4px 0;color:#555;">
          🎯 Confiance : <strong>{alert.confidence_pct}</strong>
        </p>
        <p style="margin:4px 0;color:#555;">🕐 Heure : <strong>{alert.timestamp_str}</strong></p>
        {location_row}
      </div>

      <!-- Détails -->
      {"<h3 style='color:#333;margin-bottom:8px;'>Détails des détections</h3><table style='width:100%;border-collapse:collapse;font-size:14px;'><thead><tr style='background:#f0f0f0;'><th style='padding:8px 12px;text-align:left;'>Élément</th><th style='padding:8px 12px;text-align:right;'>Confiance</th></tr></thead><tbody>" + detections_rows + "</tbody></table>" if alert.detections else ""}

      <!-- Fichier -->
      <p style="color:#888;font-size:13px;margin-top:20px;">
        📄 Fichier : <code>{alert.filename}</code>
      </p>

      <!-- Note -->
      <p style="color:#888;font-size:12px;margin-top:16px;border-top:1px solid #eee;padding-top:12px;">
        Ce message est généré automatiquement par le système de détection ENSITECH.<br>
        Conformément au RGPD, les données sont conservées 30 jours maximum.
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#f8f8f8;padding:14px 28px;text-align:center;">
      <p style="color:#aaa;font-size:12px;margin:0;">
        ENSITECH · Article 17 du Règlement Intérieur
      </p>
    </div>

  </div>
</body>
</html>"""


def _render_email_plain(alert: DressCodeAlert) -> str:
    return (
        f"ALERTE — Code Vestimentaire Non Respecté\n"
        f"=========================================\n\n"
        f"Type d'infraction : {alert.reason_label}\n"
        f"Confiance         : {alert.confidence_pct}\n"
        f"Heure             : {alert.timestamp_str}\n"
        f"Localisation      : {alert.location or 'Non précisée'}\n"
        f"Fichier           : {alert.filename}\n\n"
        f"— Système de surveillance ENSITECH (Article 17 du Règlement Intérieur)"
    )


# ---------------------------------------------------------------------------
# Service principal
# ---------------------------------------------------------------------------

class NotificationService:
    """
    Orchestre l'envoi des notifications sur tous les canaux configurés.
    Instancier une seule fois (singleton) et appeler `notify()` à chaque alerte.
    """

    def __init__(self, email_config: Optional[EmailConfig] = None) -> None:
        self._email_cfg = email_config

    # ------------------------------------------------------------------
    # Point d'entrée public
    # ------------------------------------------------------------------

    async def notify(self, alert: DressCodeAlert) -> dict:
        """
        Envoie la notification sur tous les canaux activés.
        Retourne un dict { canal: bool } indiquant le succès de chaque envoi.
        """
        results: dict[str, bool] = {}

        if self._email_cfg and self._email_cfg.enabled:
            results["email"] = self._send_email(alert)

        if not results:
            logger.warning("Aucun canal de notification configuré.")

        return results

    # ------------------------------------------------------------------
    # Email (Gmail SMTP / STARTTLS)
    # ------------------------------------------------------------------

    def _send_email(self, alert: DressCodeAlert) -> bool:
        cfg = self._email_cfg
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                f"🚨 [ENSITECH] Infraction détectée — {alert.reason_label} "
                f"({alert.confidence_pct})"
            )
            msg["From"]    = cfg.sender
            msg["To"]      = ", ".join(cfg.recipients)

            msg.attach(MIMEText(_render_email_plain(alert), "plain", "utf-8"))
            msg.attach(MIMEText(_render_email_html(alert),  "html",  "utf-8"))

            context = ssl.create_default_context()
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(cfg.sender, cfg.password)
                server.sendmail(cfg.sender, cfg.recipients, msg.as_string())

            logger.info(
                "Email envoyé à %s (infraction: %s, confiance: %s)",
                cfg.recipients, alert.reason, alert.confidence_pct,
            )
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Échec d'authentification Gmail. "
                "Vérifiez que vous utilisez un App Password "
                "et que la validation en 2 étapes est activée."
            )
        except smtplib.SMTPException as exc:
            logger.error("Erreur SMTP : %s", exc)
        except Exception as exc:
            logger.exception("Erreur inattendue lors de l'envoi email : %s", exc)

        return False


# ---------------------------------------------------------------------------
# Helpers pour instancier depuis variables d'environnement
# ---------------------------------------------------------------------------

def email_config_from_env() -> Optional[EmailConfig]:
   
    import os
    sender     = os.getenv("ENSITECH_EMAIL_SENDER")
    password   = os.getenv("ENSITECH_EMAIL_PASSWORD")
    recipients = os.getenv("ENSITECH_EMAIL_RECIPIENTS", "")
    enabled    = os.getenv("ENSITECH_EMAIL_ENABLED", "true").lower() == "true"

    if not sender or not password:
        logger.warning(
            "Variables ENSITECH_EMAIL_SENDER / ENSITECH_EMAIL_PASSWORD non définies. "
            "Notifications email désactivées."
        )
        return None

    return EmailConfig(
        sender=sender,
        password=password,
        recipients=[r.strip() for r in recipients.split(",") if r.strip()],
        enabled=enabled,
    )