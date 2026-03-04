"""
Script d'entraînement du modèle YOLOv8 pour la détection du code vestimentaire
Adapté pour le dataset Fashionpedia complet avec mapping ENSITECH

Classes détectées :
  0: short_bermuda   (short, bermuda, short de sport)
  1: jupe_courte     (jupe / mini-jupe)
  2: couvre_chef     (casquette, chapeau, bonnet, bandana)
"""

import os
from datetime import datetime
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
RESULTS_DIR = BASE_DIR / "results"

# Créer les dossiers nécessaires
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Hyperparamètres d'entraînement
TRAINING_CONFIG = {
    # -----------------------------------------------------------------------
    # Modèle de base
    # -----------------------------------------------------------------------
    # yolov8n = nano (rapide, moins précis) - bon pour les tests
    # yolov8s = small - bon compromis vitesse/précision
    # yolov8m = medium - recommandé pour la production
    # yolov8l = large - meilleure précision, plus lent
    # yolov8x = extra large - le plus précis, le plus lent
    "model_size": "yolov8s",  # Small : bon compromis pour 3 classes

    # -----------------------------------------------------------------------
    # Paramètres d'entraînement
    # -----------------------------------------------------------------------
    "epochs": 150,            # Plus d'époques car on a beaucoup de négatifs
    "batch": 32,              # Ajuster selon ta RAM/GPU (8 si peu de VRAM)
    "imgsz": 640,             # Taille standard
    "patience": 20,           # Early stopping - réduit car 3 classes seulement

    # -----------------------------------------------------------------------
    # Optimisation
    # -----------------------------------------------------------------------
    "optimizer": "AdamW",     # AdamW est généralement meilleur que Adam
    "lr0": 0.001,             # Learning rate initial (plus bas qu'avant)
    "lrf": 0.01,              # Learning rate final (lr0 * lrf)
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 5,       # Warmup pour stabiliser le début de l'entraînement

    # -----------------------------------------------------------------------
    # Augmentation de données
    # -----------------------------------------------------------------------
    "hsv_h": 0.015,           # Teinte
    "hsv_s": 0.7,             # Saturation
    "hsv_v": 0.4,             # Valeur/luminosité
    "degrees": 10.0,          # Rotation (utile pour détecter couvre-chefs inclinés)
    "translate": 0.1,         # Translation
    "scale": 0.5,             # Échelle
    "shear": 2.0,             # Léger cisaillement
    "perspective": 0.0001,    # Légère perspective
    "flipud": 0.0,            # Pas de retournement vertical
    "fliplr": 0.5,            # Retournement horizontal
    "mosaic": 1.0,            # Mosaïque (désactivé automatiquement les 10 dernières époques)
    "mixup": 0.1,             # Léger mixup pour la robustesse
    "copy_paste": 0.1,        # Copy-paste augmentation

    # -----------------------------------------------------------------------
    # Autres paramètres
    # -----------------------------------------------------------------------
    "save": True,
    "save_period": 10,        # Checkpoint tous les 10 époques
    "cache": True,           # True si RAM > 16GB pour accélérer
    "device": "auto",
    "workers": 8,
    "project": str(MODELS_DIR),
    "name": f"dress_code_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "exist_ok": True,
    "pretrained": True,
    "verbose": True,
    "plots": True,            # Générer les graphiques de métriques
    "val": True,              # Valider pendant l'entraînement
}


def check_gpu():
    """
    Vérifie la disponibilité du GPU
    """
    print("\n🔍 Vérification du matériel...")

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"✅ GPU disponible : {gpu_name}")
        print(f"   Mémoire GPU : {gpu_memory:.2f} GB")

        # Ajuster le batch size selon la VRAM
        if gpu_memory < 4:
            print("⚠️  VRAM faible, batch size recommandé : 8")
        elif gpu_memory < 8:
            print("ℹ️  VRAM correcte, batch size recommandé : 16")
        else:
            print("ℹ️  VRAM suffisante, batch size recommandé : 16-32")

        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("✅ Apple Silicon (MPS) disponible")
        return "mps"
    else:
        print("⚠️  Pas de GPU détecté, utilisation du CPU")
        print("   L'entraînement sera significativement plus lent.")
        print("   Conseil : réduire batch size à 8 et epochs à 50 pour tester")
        return "cpu"


def load_dataset_config():
    """
    Charge et vérifie la configuration du dataset
    """
    yaml_path = DATA_PROCESSED / "data.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError(
            f"❌ Fichier de configuration non trouvé : {yaml_path}\n"
            "Veuillez d'abord exécuter : python scripts/prepare_dataset.py"
        )

    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print(f"\n📊 Configuration du dataset :")
    print(f"   Nombre de classes : {config['nc']}")
    print(f"   Classes :")
    for i, name in enumerate(config['names']):
        print(f"     [{i}] {name}")
    print(f"   Chemin : {config['path']}")

    # Vérifier que les dossiers existent et contiennent des fichiers
    base_path = Path(config['path'])
    for split in ['train', 'val']:
        img_dir = base_path / split / 'images'
        lbl_dir = base_path / split / 'labels'
        if img_dir.exists():
            n_images = len(list(img_dir.glob('*.jpg')))
            n_labels = len(list(lbl_dir.glob('*.txt')))

            # Compter les labels non vides (images avec violations)
            n_positive = sum(
                1 for f in lbl_dir.glob('*.txt') if f.stat().st_size > 0
            )
            print(f"   {split}: {n_images} images, {n_labels} labels ({n_positive} positifs)")
        else:
            print(f"   ⚠️  Dossier manquant : {img_dir}")

    return yaml_path


def train_model(yaml_path, device):
    """
    Entraîne le modèle YOLO
    """
    print("\n" + "=" * 60)
    print("DÉMARRAGE DE L'ENTRAÎNEMENT")
    print("=" * 60)

    # Charger le modèle pré-entraîné
    model_name = f"{TRAINING_CONFIG['model_size']}.pt"
    print(f"\n📦 Chargement du modèle : {model_name}")
    model = YOLO(model_name)

    print(f"\n⚙️  Configuration :")
    print(f"   Modèle : {TRAINING_CONFIG['model_size']}")
    print(f"   Époques : {TRAINING_CONFIG['epochs']}")
    print(f"   Batch size : {TRAINING_CONFIG['batch']}")
    print(f"   Taille image : {TRAINING_CONFIG['imgsz']}")
    print(f"   Optimizer : {TRAINING_CONFIG['optimizer']}")
    print(f"   Learning rate : {TRAINING_CONFIG['lr0']} -> {TRAINING_CONFIG['lr0'] * TRAINING_CONFIG['lrf']}")
    print(f"   Device : {device}")

    # Préparer les paramètres d'entraînement
    train_params = TRAINING_CONFIG.copy()
    train_params["data"] = str(yaml_path)
    train_params["device"] = device if device != "auto" else None

    # Retirer les paramètres non supportés par train()
    train_params.pop("model_size", None)

    print(f"\n🚀 Début de l'entraînement...")
    print("   (Temps estimé : 1-4h avec GPU, 10-24h avec CPU)")

    try:
        results = model.train(**train_params)

        print("\n" + "=" * 60)
        print("✅ ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS !")
        print("=" * 60)

        # Métriques finales
        print(f"\n📊 Résultats finaux :")
        metrics = results.results_dict
        print(f"   mAP50 : {metrics.get('metrics/mAP50(B)', 'N/A'):.4f}")
        print(f"   mAP50-95 : {metrics.get('metrics/mAP50-95(B)', 'N/A'):.4f}")
        print(f"   Precision : {metrics.get('metrics/precision(B)', 'N/A'):.4f}")
        print(f"   Recall : {metrics.get('metrics/recall(B)', 'N/A'):.4f}")

        # Chemin du meilleur modèle
        best_model_path = (
            Path(train_params["project"]) / train_params["name"] / "weights" / "best.pt"
        )
        print(f"\n💾 Meilleur modèle : {best_model_path}")

        # Copier le meilleur modèle
        final_dir = MODELS_DIR / "final"
        final_dir.mkdir(exist_ok=True)
        final_model_path = final_dir / "best_model.pt"

        if best_model_path.exists():
            import shutil
            shutil.copy(best_model_path, final_model_path)
            print(f"💾 Copie finale : {final_model_path}")

        print(f"\n📌 Prochaine étape : python scripts/validate.py")
        print(f"   ou testez avec : python scripts/detect_webcam.py")

        return results

    except Exception as e:
        print(f"\n❌ Erreur lors de l'entraînement : {e}")
        raise


def main():
    """
    Fonction principale
    """
    print("=" * 60)
    print("ENTRAÎNEMENT YOLO - Code Vestimentaire ENSITECH")
    print("Version 2 : Dataset Fashionpedia complet (46 catégories)")
    print("=" * 60)

    # Vérifier le GPU
    device = check_gpu()

    # Charger la configuration du dataset
    yaml_path = load_dataset_config()

    # Avertissement
    print("\n" + "=" * 60)
    print("⚠️  INFORMATION")
    print("=" * 60)
    print("Classes détectées :")
    print("  [0] short_bermuda - Short, bermuda")
    print("  [1] jupe_courte   - Jupe (potentiellement mini-jupe)")
    print("  [2] couvre_chef   - Casquette, chapeau, bonnet, bandana")
    print()
    print("L'entraînement peut prendre plusieurs heures.")
    print("Assurez-vous d'avoir :")
    print("  - Suffisamment d'espace disque (~5-10 GB)")
    print("  - Une connexion stable")

    response = input("\n▶️  Voulez-vous continuer ? (o/n) : ").strip().lower()

    if response != "o":
        print("\n❌ Entraînement annulé.")
        return

    # Entraîner
    results = train_model(yaml_path, device)

    print("\n🎉 Terminé ! Vous pouvez maintenant tester votre modèle.")


if __name__ == "__main__":
    main()