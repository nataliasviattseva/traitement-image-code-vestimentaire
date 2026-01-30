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

# =============================================================================
# CONFIGURATION OPTIMISÉE POUR :
# - GPU : RTX 3070 Ti (8 Go VRAM)
# - RAM : 32 Go
# - CPU : Intel i7-12700K (12 cores / 20 threads)
# =============================================================================

TRAINING_CONFIG = {
    # Modèle de base - YOLO11 (dernière version Ultralytics)
    # Options: yolo11n, yolo11s, yolo11m, yolo11l, yolo11x
    # n = nano (plus rapide, moins précis)
    # s = small (bon compromis vitesse/précision)
    # m = medium (meilleure précision, plus lent) ← RECOMMANDÉ pour +précision
    # l = large (nécessite plus de VRAM)
    # x = extra large (plus lent, plus précis)
    "model_size": "yolo11m",  # YOLO11 Medium = +2-5% mAP vs YOLOv8
    
    # Paramètres d'entraînement - OPTIMISÉS RTX 3070 Ti (8 Go VRAM)
    "epochs": 150,  # Plus d'époques pour une meilleure convergence
    "batch": 16,  # Réduit pour YOLOv8m (modèle plus gros)
    "imgsz": 640,  # Taille standard, bon compromis vitesse/précision
    "patience": 50,  # Early stopping augmenté - plus de temps pour converger
    
    # Optimisation - AdamW recommandé pour YOLO
    "optimizer": "AdamW",  # Meilleur que Adam pour la régularisation
    "lr0": 0.005,  # Learning rate initial (réduit pour meilleure convergence)
    "lrf": 0.001,  # Learning rate final (lr0 * lrf)
    "momentum": 0.937,  # Momentum SGD
    "weight_decay": 0.0005,  # Weight decay (régularisation L2)
    "warmup_epochs": 3.0,  # Époques de warmup pour stabiliser le début
    "warmup_momentum": 0.8,  # Momentum pendant le warmup
    "warmup_bias_lr": 0.1,  # Learning rate du biais pendant warmup
    
    # Augmentation de données - RENFORCÉ pour meilleure précision
    "hsv_h": 0.02,  # Augmentation de teinte (couleurs des vêtements)
    "hsv_s": 0.8,  # Augmentation de saturation (augmenté)
    "hsv_v": 0.5,  # Augmentation de valeur/luminosité (augmenté)
    "degrees": 15.0,  # Rotation augmentée (accessoires = angles variés)
    "translate": 0.15,  # Translation d'image (augmenté)
    "scale": 0.6,  # Échelle d'image (augmenté pour petits objets)
    "shear": 3.0,  # Cisaillement augmenté
    "perspective": 0.0002,  # Légère perspective
    "flipud": 0.0,  # Pas de retournement vertical (personnes)
    "fliplr": 0.5,  # Retournement horizontal OK
    "mosaic": 1.0,  # Augmentation mosaïque (très efficace)
    "mixup": 0.2,  # Augmentation mixup renforcée
    "copy_paste": 0.2,  # Copy-paste augmentation renforcée (aide petits objets)
    
    # Performance - OPTIMISÉ pour 32 Go RAM + i7-12700K
    "save": True,  # Sauvegarder les checkpoints
    "save_period": 10,  # Sauvegarder tous les 10 époques
    "cache": "ram",  # ✅ ACTIVÉ - Cache images en RAM (32 Go = largement suffisant)
    "device": "0",  # GPU 0 (ta RTX 3070 Ti)
    "workers": 12,  # ✅ Optimisé pour i7-12700K (12 cores physiques)
    "amp": True,  # ✅ Mixed Precision - Accélère l'entraînement sur RTX 30xx
    "rect": False,  # Rectangular training (False = plus stable)
    "cos_lr": True,  # ✅ Cosine LR scheduler (meilleure convergence)
    "close_mosaic": 10,  # Désactive mosaic les 10 dernières époques
    
    # Sauvegarde et logs
    "project": str(MODELS_DIR),
    "name": f"dress_code_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "exist_ok": True,
    "pretrained": True,
    "verbose": True,
    "plots": True,  # Génère les graphiques d'entraînement
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
