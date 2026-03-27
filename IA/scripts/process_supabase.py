"""
Script de traitement des images stockées en base Supabase.

Flux:
1) Lire les images non traitées depuis `images`
2) Télécharger chaque image via son URL
3) Exécuter l'inférence YOLO
4) Insérer les détections dans `violations`
5) Mettre à jour `images.traite` et `images.traite_at`
"""

import argparse
import base64
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import ssl
from urllib import parse, request

import certifi

import cv2
import numpy as np
import cloudinary
import cloudinary.uploader
from supabase import Client, create_client
from ultralytics import YOLO

# Configuration locale du projet IA
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"


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

    def fetch_unprocessed_images(self, limit: int) -> list[dict[str, Any]]:
        response = (
            self.client.table("images")
            .select("id,url")
            .eq("traite", False)
            .order("uploaded_at", desc=False)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def insert_violations(self, violations: list[dict[str, Any]]) -> None:
        if not violations:
            return
        self.client.table("violations").insert(violations).execute()

    def mark_image_processed(self, image_id: str) -> None:
        traite_at = datetime.now(timezone.utc).isoformat()
        (
            self.client.table("images")
            .update({"traite": True, "traite_at": traite_at})
            .eq("id", image_id)
            .execute()
        )

    def update_image_url(self, image_id: str, column_name: str, image_url: str) -> None:
        (
            self.client.table("images")
            .update({column_name: image_url})
            .eq("id", image_id)
            .execute()
        )


def load_model(model_path: str | None = None) -> YOLO:
    """
    Charge le modèle YOLO.
    - Si model_path est fourni, il est prioritaire.
    - Sinon, essaie IA/models/final/best_model.pt
    - Sinon, prend le best.pt le plus récent.
    """
    if model_path:
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"❌ Modèle introuvable: {path}")
        print(f"✅ Chargement du modèle: {path}")
        return YOLO(str(path))

    final_model = MODELS_DIR / "final" / "best_model.pt"
    if final_model.exists():
        print(f"✅ Chargement du modèle: {final_model}")
        return YOLO(str(final_model))

    model_dirs = list(MODELS_DIR.glob("dress_code_*"))
    if not model_dirs:
        raise FileNotFoundError(
            "❌ Aucun modèle trouvé. "
            "Fournis --model-path ou entraîne un modèle avec scripts/train.py"
        )

    latest_dir = max(model_dirs, key=lambda p: p.stat().st_mtime)
    best_model = latest_dir / "weights" / "best.pt"
    if not best_model.exists():
        raise FileNotFoundError(f"❌ Modèle introuvable dans {latest_dir}")

    print(f"✅ Chargement du modèle: {best_model}")
    return YOLO(str(best_model))


def download_image_as_array(image_url: str) -> np.ndarray:
    """Télécharge une image URL et la convertit en ndarray BGR (OpenCV)."""
    req = request.Request(
        image_url,
        headers={"User-Agent": "dress-code-ai/1.0"},
        method="GET",
    )
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    with request.urlopen(req, timeout=30, context=ssl_ctx) as response:
        image_bytes = response.read()

    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Image invalide ou non décodable.")
    return image


def build_violations_payload(
    image_id: str, model: YOLO, result: Any
) -> list[dict[str, Any]]:
    """Transforme les détections YOLO en lignes pour la table `violations`."""
    payload: list[dict[str, Any]] = []
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = str(model.names[class_id])

        x1, y1, x2, y2 = box.xyxy[0].tolist()
        bbox_x = float(x1)
        bbox_y = float(y1)
        bbox_w = float(max(0.0, x2 - x1))
        bbox_h = float(max(0.0, y2 - y1))

        payload.append(
            {
                "image_id": image_id,
                "classe": class_name,
                "confiance": confidence,
                "bbox_x": bbox_x,
                "bbox_y": bbox_y,
                "bbox_w": bbox_w,
                "bbox_h": bbox_h,
            }
        )
    return payload


def upload_annotated_to_cloudinary(
    annotated_image: np.ndarray,
    image_id: str,
    cloudinary_folder: str,
) -> str:
    """Upload une image annotée vers Cloudinary et retourne son URL HTTPS sécurisée."""
    ok, encoded = cv2.imencode(".jpg", annotated_image)
    if not ok:
        raise RuntimeError("Échec d'encodage JPEG de l'image annotée.")

    image_b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
    data_uri = f"data:image/jpeg;base64,{image_b64}"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    upload_result = cloudinary.uploader.upload(
        data_uri,
        folder=cloudinary_folder,
        public_id=f"{image_id}_{timestamp}",
        overwrite=True,
        resource_type="image",
    )
    secure_url = upload_result.get("secure_url")
    if not secure_url:
        raise RuntimeError("Cloudinary n'a pas renvoyé d'URL sécurisée.")
    return str(secure_url)


def configure_cloudinary_from_env() -> None:
    """
    Configure Cloudinary depuis l'environnement.
    Priorité:
    1) CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
    2) CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET
    """
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    if cloudinary_url:
        parsed = parse.urlparse(cloudinary_url)
        api_key = parse.unquote(parsed.username or "")
        api_secret = parse.unquote(parsed.password or "")
        cloud_name = (parsed.hostname or "").strip()

        if not all([api_key, api_secret, cloud_name]):
            raise EnvironmentError(
                "❌ CLOUDINARY_URL invalide. "
                "Format attendu: cloudinary://<api_key>:<api_secret>@<cloud_name>"
            )

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        return

    cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET")
    if not all([cloudinary_cloud_name, cloudinary_api_key, cloudinary_api_secret]):
        raise EnvironmentError(
            "❌ Variables Cloudinary manquantes.\n"
            "Définis soit CLOUDINARY_URL, soit "
            "CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET."
        )

    cloudinary.config(
        cloud_name=cloudinary_cloud_name,
        api_key=cloudinary_api_key,
        api_secret=cloudinary_api_secret,
        secure=True,
    )


def process_images(
    model: YOLO,
    client: SupabaseDbClient,
    batch_size: int,
    conf_threshold: float,
    update_url_column: str,
    cloudinary_folder: str,
) -> None:
    images = client.fetch_unprocessed_images(limit=batch_size)
    if not images:
        print("ℹ️ Aucune image non traitée trouvée.")
        return

    print(f"📥 {len(images)} image(s) récupérée(s) depuis Supabase.")
    processed = 0
    with_violations = 0
    failures = 0

    for item in images:
        image_id = item["id"]
        image_url = item["url"]
        print(f"\n🖼️ Traitement image {image_id}")

        try:
            image = download_image_as_array(image_url)
            results = model.predict(
                source=image,
                conf=conf_threshold,
                save=False,
                verbose=False,
            )
            result = results[0]
            violations = build_violations_payload(image_id=image_id, model=model, result=result)

            if violations:
                client.insert_violations(violations)
                with_violations += 1
                print(f"⚠️ {len(violations)} violation(s) détectée(s).")
                annotated_image = result.plot()
                cloudinary_url = upload_annotated_to_cloudinary(
                    annotated_image=annotated_image,
                    image_id=str(image_id),
                    cloudinary_folder=cloudinary_folder,
                )
                client.update_image_url(
                    image_id=image_id,
                    column_name=update_url_column,
                    image_url=cloudinary_url,
                )
                print(f"☁️ URL Cloudinary enregistrée: {cloudinary_url}")
            else:
                print("✅ Aucune violation détectée.")

            client.mark_image_processed(image_id)
            processed += 1

        except Exception as exc:
            failures += 1
            print(f"❌ Erreur sur image {image_id}: {exc}")

    print("\n" + "=" * 60)
    print("Traitement terminé")
    print("=" * 60)
    print(f"Images traitées: {processed}")
    print(f"Images avec violation: {with_violations}")
    print(f"Échecs: {failures}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Traite les images Supabase avec le modèle YOLO."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Nombre max d'images non traitées à traiter par exécution.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.5,
        help="Seuil de confiance YOLO (0.0 - 1.0).",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Chemin explicite vers un modèle YOLO (.pt).",
    )
    parser.add_argument(
        "--image-url-column",
        type=str,
        default=os.getenv("SUPABASE_ANNOTATED_URL_COLUMN", "url"),
        help="Colonne de `images` où stocker l'URL Cloudinary (défaut: SUPABASE_ANNOTATED_URL_COLUMN ou url).",
    )
    parser.add_argument(
        "--cloudinary-folder",
        type=str,
        default=os.getenv("CLOUDINARY_FOLDER", "dress-code-violations"),
        help="Dossier Cloudinary de destination.",
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

    configure_cloudinary_from_env()

    print("=" * 60)
    print("Traitement Supabase - Détection code vestimentaire")
    print("=" * 60)

    model = load_model(args.model_path)
    supabase_client = create_client(supabase_url, supabase_key)
    client = SupabaseDbClient(client=supabase_client)

    process_images(
        model=model,
        client=client,
        batch_size=args.batch_size,
        conf_threshold=args.conf,
        update_url_column=args.image_url_column,
        cloudinary_folder=args.cloudinary_folder,
    )


if __name__ == "__main__":
    main()
