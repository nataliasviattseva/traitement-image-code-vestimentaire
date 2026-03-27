"""
Script d'envoi des alertes pour les violations détectées.

Flux:
1) Récupérer les images traitées mais non notifiées (images.notifie = false)
     qui ont au moins une violation dans `violations`
2) Pour chaque image, insérer une ligne dans `alertes` par type (email, push)
     avec le statut (sent / failed)
3) Mettre à jour images.notifie = true pour éviter les doublons
"""

import argparse
import os
import smtplib
from pathlib import Path
from typing import Any
from urllib import parse
from email.message import EmailMessage

from supabase import Client, create_client

# Configuration locale du projet IA
BASE_DIR = Path(__file__).parent.parent


def load_dotenv_file(dotenv_path: Path) -> None:
    """Charge un fichier .env simple dans os.environ (sans écraser l'existant)."""
    if not dotenv_path.exists():
        return

    with dotenv_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def normalize_supabase_url(raw_url: str | None) -> str | None:
    """
    Normalise SUPABASE_URL en URL HTTP projet Supabase.
    Accepte:
    - https://<project-ref>.supabase.co
    - postgresql://...@db.<project-ref>.supabase.co:5432/postgres
    """
    if not raw_url:
        return None

    value = raw_url.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value

    if value.startswith("postgresql://"):
        parsed = parse.urlparse(value)
        host = parsed.hostname or ""
        # Format attendu: db.<project-ref>.supabase.co
        parts = host.split(".")
        if len(parts) >= 4 and parts[0] == "db" and parts[-2] == "supabase" and parts[-1] == "co":
            project_ref = parts[1]
            return f"https://{project_ref}.supabase.co"

    return value


class SupabaseDbClient:
    """Client Supabase via SDK officiel supabase-py."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def fetch_unnotified_images(self) -> list[dict[str, Any]]:
        """
        Retourne les images (id, url) traitées, non notifiées,
        ayant au moins une violation.
        Jointure interne violations → images pour ne retenir que les images avec détections.
        """
        response = (
            self.client.table("images")
            .select("id,url,violations!inner(classe)")
            .eq("notifie", False)
            .eq("traite", True)
            .execute()
        )
        rows = response.data or []
        payload: list[dict[str, Any]] = []
        for row in rows:
            image_id = row.get("id")
            if not image_id:
                continue

            raw_violations = row.get("violations") or []
            classes = sorted(
                {
                    str(v.get("classe")).strip()
                    for v in raw_violations
                    if isinstance(v, dict) and v.get("classe")
                }
            )
            payload.append(
                {
                    "id": image_id,
                    "url": row.get("url") or "",
                    "violation_classes": classes,
                }
            )

        return payload

    def insert_alert(self, alert: dict[str, Any]) -> None:
        self.client.table("alertes").insert(alert).execute()

    def mark_image_notified(self, image_id: str) -> None:
        (
            self.client.table("images")
            .update({"notifie": True})
            .eq("id", image_id)
            .execute()
        )


class EmailSender:
    """Envoi SMTP des alertes email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        smtp_from: str,
        recipient: str,
        use_tls: bool,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.recipient = recipient
        self.use_tls = use_tls

    def send_violation_alert(
        self,
        image_id: str,
        image_url: str | None = None,
        violation_classes: list[str] | None = None,
    ) -> None:
        message = EmailMessage()
        message["Subject"] = "Alerte code vestimentaire"
        message["From"] = self.smtp_from
        message["To"] = self.recipient
        image_url_text = image_url or "URL indisponible"
        html_image_block = (
            f'<p><img src="{image_url}" alt="Image en violation" '
            'style="max-width:100%;height:auto;border-radius:8px;" /></p>'
            if image_url
            else "<p><em>URL image indisponible.</em></p>"
        )
        classes = violation_classes or []
        classes_text = ", ".join(classes) if classes else "Non disponible"
        classes_html = (
            "<ul>"
            + "".join(f"<li><strong>{class_name}</strong></li>" for class_name in classes)
            + "</ul>"
            if classes
            else "<p><em>Classes non disponibles.</em></p>"
        )
        message.set_content(
            (
                "Une violation potentielle du code vestimentaire a ete detectee.\n\n"
                f"Image ID: {image_id}\n"
                f"Image URL: {image_url_text}\n"
                f"Classe(s) detectee(s): {classes_text}\n"
                "Merci de verifier dans votre tableau de bord Supabase."
            )
        )
        message.add_alternative(
            f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #222;">
                <h2 style="margin-bottom: 12px;">Alerte code vestimentaire</h2>
                <p>Une violation potentielle du code vestimentaire a ete detectee.</p>
                <p><strong>Image ID:</strong> {image_id}</p>
                <p><strong>Image URL:</strong>
                  <a href="{image_url_text}">{image_url_text}</a>
                </p>
                <p><strong>Classe(s) detectee(s):</strong></p>
                {classes_html}
                {html_image_block}
                <p>Merci de verifier dans votre tableau de bord Supabase.</p>
              </body>
            </html>
            """,
            subtype="html",
        )

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
            if self.use_tls:
                smtp.starttls()
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.send_message(message)


def build_alert_payload(
    image_id: str,
    alert_type: str,
    statut: str,
) -> dict[str, Any]:
    """Construit une ligne pour la table `alertes`.
    envoye_at est géré automatiquement par la DB (DEFAULT now()).
    """
    return {
        "image_id": image_id,
        "type": alert_type,
        "statut": statut,
    }


def send_alerts(
    client: SupabaseDbClient,
    alert_types: list[str],
    email_sender: EmailSender | None = None,
) -> None:
    images = client.fetch_unnotified_images()

    if not images:
        print("ℹ️ Aucune image avec violation non notifiée.")
        return

    print(f"📋 {len(images)} image(s) à notifier.")

    notified = 0
    failures = 0

    for item in images:
        image_id = item["id"]
        image_url = item.get("url", "")
        violation_classes = item.get("violation_classes", [])
        print(f"\n🔔 Notification image {image_id}")
        image_ok = True

        for alert_type in alert_types:
            statut = "unsend" if alert_type == "push" else "sent"
            try:
                if alert_type == "email":
                    if email_sender is None:
                        raise RuntimeError(
                            "Configuration email absente. Definis ALERT_EMAIL_TO et SMTP_*."
                        )
                    email_sender.send_violation_alert(
                        image_id=image_id,
                        image_url=image_url,
                        violation_classes=violation_classes,
                    )
                    print("  📧 Email envoye.")

                alert = build_alert_payload(
                    image_id=image_id,
                    alert_type=alert_type,
                    statut=statut,
                )
                client.insert_alert(alert)
                print(f"  ✅ Alerte [{alert_type}] insérée.")
            except Exception as exc:
                statut = "failed"
                image_ok = False
                print(f"  ❌ Erreur alerte [{alert_type}]: {exc}")
                # Insère quand même une ligne avec statut failed pour traçabilité
                try:
                    alert = build_alert_payload(
                        image_id=image_id,
                        alert_type=alert_type,
                        statut=statut,
                    )
                    client.insert_alert(alert)
                except Exception:
                    pass

        if image_ok:
            try:
                client.mark_image_notified(image_id)
                notified += 1
                print(f"  ✅ images.notifie = true")
            except Exception as exc:
                failures += 1
                print(f"  ❌ Impossible de marquer l'image comme notifiée: {exc}")
        else:
            failures += 1

    print("\n" + "=" * 60)
    print("Envoi des alertes terminé")
    print("=" * 60)
    print(f"Images notifiées: {notified}")
    print(f"Échecs: {failures}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Envoie les alertes pour les violations détectées non encore notifiées."
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=["email", "push"],
        choices=["email", "push"],
        help="Types d'alertes à créer (défaut: email push).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Charge automatiquement IA/.env si présent.
    load_dotenv_file(BASE_DIR / ".env")

    supabase_url = normalize_supabase_url(os.getenv("SUPABASE_URL"))
    supabase_key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )

    if not supabase_url or not supabase_key:
        raise EnvironmentError(
            "❌ Variables manquantes: SUPABASE_URL et une clé Supabase.\n"
            "Exemple:\n"
            "export SUPABASE_URL='https://xxxx.supabase.co'\n"
            "export SUPABASE_SECRET_KEY='service_role_or_anon_key'"
        )

    if "supabase.co" not in supabase_url or not supabase_url.startswith("http"):
        raise EnvironmentError(
            "❌ SUPABASE_URL invalide.\n"
            "Attendu: URL HTTP du projet Supabase (ex: https://xxxx.supabase.co), "
            "pas l'URL PostgreSQL."
        )

    print("=" * 60)
    print("Envoi des alertes - Violations code vestimentaire")
    print("=" * 60)
    print(f"Types d'alertes: {args.types}")

    email_sender: EmailSender | None = None
    if "email" in args.types:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port_raw = os.getenv("SMTP_PORT", "587")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM") or smtp_user
        email_to = os.getenv("ALERT_EMAIL_TO")
        smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {
            "0",
            "false",
            "no",
        }

        if not all([smtp_host, smtp_user, smtp_password, smtp_from, email_to]):
            raise EnvironmentError(
                "❌ Configuration email incomplete.\n"
                "Variables requises: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, "
                "SMTP_FROM (ou SMTP_USER), ALERT_EMAIL_TO."
            )

        try:
            smtp_port = int(smtp_port_raw)
        except ValueError as exc:
            raise EnvironmentError("❌ SMTP_PORT doit etre un entier valide.") from exc

        email_sender = EmailSender(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_from=smtp_from,
            recipient=email_to,
            use_tls=smtp_use_tls,
        )

    supabase_client = create_client(supabase_url, supabase_key)
    client = SupabaseDbClient(client=supabase_client)

    send_alerts(client=client, alert_types=args.types, email_sender=email_sender)


if __name__ == "__main__":
    main()