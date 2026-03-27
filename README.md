# Détection de Code Vestimentaire - Module IA

Module IA pour détecter les infractions au code vestimentaire avec YOLOv8, traiter des images stockées dans Supabase, générer une image annotée, l'uploader sur Cloudinary, puis notifier les violations.

## Vue d'ensemble du flux

1. `scripts/process_supabase.py` lit les images `images.traite = false` depuis Supabase.
2. Le modèle YOLO détecte les violations.
3. Les détections sont insérées dans `violations`.
4. Si violation :
   - une image annotée (bbox) est générée,
   - l'image est uploadée sur Cloudinary,
   - l'URL HTTPS Cloudinary est enregistrée dans `images` (colonne configurable).
5. L'image est marquée traitée (`traite = true`, `traite_at`).
6. `scripts/send_alerts.py` peut ensuite envoyer les alertes email/push.

## Installation

```bash
cd IA
source venv/bin/activate  # macOS/Linux
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration `.env`

Créer/compléter `IA/.env` :

```env
# Supabase
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SECRET_KEY=<service_role_or_secret_key>

# Cloudinary (option 1 recommandée)
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>

# Optionnel Cloudinary
CLOUDINARY_FOLDER=dress-code-violations

# Colonne Supabase à mettre à jour avec l'URL annotée
# Par défaut: url
SUPABASE_ANNOTATED_URL_COLUMN=url

# Email alertes (si send_alerts.py utilisé)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<app_password>
SMTP_FROM=<email>
SMTP_USE_TLS=true
ALERT_EMAIL_TO=<destinataire>
```

Alternative Cloudinary (si pas de `CLOUDINARY_URL`) :

```env
CLOUDINARY_CLOUD_NAME=<cloud_name>
CLOUDINARY_API_KEY=<api_key>
CLOUDINARY_API_SECRET=<api_secret>
```

## Utilisation

### 1) Traitement Supabase + YOLO + Cloudinary

```bash
python scripts/process_supabase.py
```

Options utiles :

```bash
# Colonne ciblée dans la table images
python scripts/process_supabase.py --image-url-column url_annotee

# Dossier Cloudinary
python scripts/process_supabase.py --cloudinary-folder dress-code-violations

# Seuil de confiance
python scripts/process_supabase.py --conf 0.5

# Taille de lot
python scripts/process_supabase.py --batch-size 20
```

### 2) Envoi des alertes

```bash
python scripts/send_alerts.py --types email push
```

## Scripts principaux

- `scripts/download_data.py` : téléchargement du dataset.
- `scripts/prepare_dataset.py` : préparation/annotations YOLO.
- `scripts/train.py` : entraînement du modèle.
- `scripts/validate.py` : validation.
- `scripts/inference.py` : inférence image/vidéo/webcam.
- `scripts/process_supabase.py` : pipeline DB Supabase + Cloudinary.
- `scripts/send_alerts.py` : alertes email/push.

## Points importants

- L'URL Cloudinary remplace la colonne choisie uniquement si au moins une violation est détectée.
- Si la colonne ciblée est `url` (défaut), l'URL d'origine est écrasée pour les images en violation.
- Pour conserver l'URL d'origine, utiliser une colonne dédiée (ex: `url_annotee`) :
  - `SUPABASE_ANNOTATED_URL_COLUMN=url_annotee`
  - ou `--image-url-column url_annotee`

## Dépannage rapide

- Erreur `Must supply api_key` :
  - vérifier `CLOUDINARY_URL`,
  - redémarrer le terminal,
  - supprimer d'anciennes variables d'env en conflit (`CLOUDINARY_API_KEY`, etc.).

- Erreur module manquant :
  - `pip install -r requirements.txt`
