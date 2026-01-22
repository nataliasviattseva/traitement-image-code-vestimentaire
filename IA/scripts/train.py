"""
Script d'entraînement du modèle YOLOv8 pour la détection du code vestimentaire
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
    # Modèle de base (options: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
    # n = nano (plus rapide, moins précis)
    # s = small
    # m = medium
    # l = large
    # x = extra large (plus lent, plus précis)
    "model_size": "yolov8n",  # Commencer avec nano pour des tests rapides
    # Paramètres d'entraînement
    "epochs": 100,  # Nombre d'époques (augmenter à 100-300 pour production)
    "batch": 16,  # Taille du batch (ajuster selon RAM/GPU)
    "imgsz": 640,  # Taille des images d'entrée
    "patience": 50,  # Early stopping patience
    # Optimisation
    "optimizer": "Adam",  # Options: SGD, Adam, AdamW
    "lr0": 0.01,  # Learning rate initial
    "lrf": 0.01,  # Learning rate final (lr0 * lrf)
    "momentum": 0.937,  # Momentum SGD
    "weight_decay": 0.0005,  # Weight decay
    # Augmentation de données
    "hsv_h": 0.015,  # Augmentation de teinte
    "hsv_s": 0.7,  # Augmentation de saturation
    "hsv_v": 0.4,  # Augmentation de valeur
    "degrees": 0.0,  # Rotation d'image
    "translate": 0.1,  # Translation d'image
    "scale": 0.5,  # Échelle d'image
    "shear": 0.0,  # Cisaillement d'image
    "perspective": 0.0,  # Perspective d'image
    "flipud": 0.0,  # Retournement vertical
    "fliplr": 0.5,  # Retournement horizontal
    "mosaic": 1.0,  # Augmentation mosaïque
    "mixup": 0.0,  # Augmentation mixup
    # Autres paramètres
    "save": True,  # Sauvegarder les checkpoints
    "save_period": 10,  # Sauvegarder tous les N époques
    "cache": False,  # Cache les images en RAM (True si RAM > 16GB)
    "device": "auto",  # 'auto', 'cpu', '0', '0,1,2,3' pour multi-GPU
    "workers": 8,  # Nombre de workers pour le DataLoader
    "project": str(MODELS_DIR),
    "name": f"dress_code_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "exist_ok": True,
    "pretrained": True,
    "verbose": True,
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
        return "cuda"
    elif torch.backends.mps.is_available():
        print("✅ Apple Silicon (MPS) disponible")
        return "mps"
    else:
        print("⚠️  Pas de GPU détecté, utilisation du CPU")
        print("   L'entraînement sera plus lent.")
        return "cpu"


def load_dataset_config():
    """
    Charge la configuration du dataset
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
    print(f"   Classes : {', '.join(config['names'])}")
    print(f"   Chemin : {config['path']}")

    return yaml_path


def train_model(yaml_path, device):
    """
    Entraîne le modèle YOLO

    Args:
        yaml_path: Chemin vers le fichier de configuration du dataset
        device: Device à utiliser ('cpu', 'cuda', 'mps')
    """
    print("\n" + "=" * 60)
    print("DÉMARRAGE DE L'ENTRAÎNEMENT")
    print("=" * 60)

    # Charger le modèle pré-entraîné
    model_name = f"{TRAINING_CONFIG['model_size']}.pt"
    print(f"\n📦 Chargement du modèle : {model_name}")
    model = YOLO(model_name)

    print(f"\n⚙️  Configuration de l'entraînement :")
    print(f"   Époques : {TRAINING_CONFIG['epochs']}")
    print(f"   Batch size : {TRAINING_CONFIG['batch']}")
    print(f"   Taille d'image : {TRAINING_CONFIG['imgsz']}")
    print(f"   Optimizer : {TRAINING_CONFIG['optimizer']}")
    print(
        f"   Learning rate : {TRAINING_CONFIG['lr0']} -> {TRAINING_CONFIG['lr0'] * TRAINING_CONFIG['lrf']}"
    )
    print(f"   Device : {device}")

    # Préparer les paramètres d'entraînement
    train_params = TRAINING_CONFIG.copy()
    train_params["data"] = str(yaml_path)
    train_params["device"] = device if device != "auto" else None

    # Retirer les paramètres non supportés par train()
    train_params.pop("model_size", None)

    print(f"\n🚀 Début de l'entraînement...")
    print("   (Cela peut prendre plusieurs heures selon votre matériel)")

    try:
        # Entraîner le modèle
        results = model.train(**train_params)

        print("\n" + "=" * 60)
        print("✅ ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS !")
        print("=" * 60)

        # Afficher les métriques finales
        print(f"\n📊 Résultats finaux :")
        print(f"   mAP50 : {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
        print(f"   mAP50-95 : {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")
        print(
            f"   Precision : {results.results_dict.get('metrics/precision(B)', 'N/A')}"
        )
        print(f"   Recall : {results.results_dict.get('metrics/recall(B)', 'N/A')}")

        # Chemin du meilleur modèle
        best_model_path = (
            Path(train_params["project"]) / train_params["name"] / "weights" / "best.pt"
        )
        print(f"\n💾 Meilleur modèle sauvegardé : {best_model_path}")

        # Copier le meilleur modèle dans models/final/
        final_dir = MODELS_DIR / "final"
        final_dir.mkdir(exist_ok=True)
        final_model_path = final_dir / "best_model.pt"

        if best_model_path.exists():
            import shutil

            shutil.copy(best_model_path, final_model_path)
            print(f"💾 Copie du modèle final : {final_model_path}")

        print(f"\n📌 Prochaine étape : python scripts/validate.py")

        return results

    except Exception as e:
        print(f"\n❌ Erreur lors de l'entraînement : {e}")
        raise


def main():
    """
    Fonction principale
    """
    print("=" * 60)
    print("ENTRAÎNEMENT DU MODÈLE YOLO")
    print("Détection du Code Vestimentaire ENSITECH")
    print("=" * 60)

    # Vérifier le GPU
    device = check_gpu()

    # Charger la configuration du dataset
    yaml_path = load_dataset_config()

    # Demander confirmation
    print("\n" + "=" * 60)
    print("⚠️  ATTENTION")
    print("=" * 60)
    print("L'entraînement peut prendre plusieurs heures.")
    print("Assurez-vous d'avoir :")
    print("  - Suffisamment d'espace disque (~5-10 GB)")
    print("  - Une connexion stable (pour télécharger le modèle)")
    print("  - De ne pas éteindre votre ordinateur")

    response = input("\n▶️  Voulez-vous continuer ? (o/n) : ").strip().lower()

    if response != "o":
        print("\n❌ Entraînement annulé.")
        return

    # Entraîner le modèle
    results = train_model(yaml_path, device)

    print("\n🎉 Tout est terminé ! Vous pouvez maintenant valider votre modèle.")


if __name__ == "__main__":
    main()
