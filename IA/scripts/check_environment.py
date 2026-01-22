"""
Script de vérification de l'environnement
Vérifie que toutes les dépendances sont installées et fonctionnelles
"""

import sys
from pathlib import Path


def print_header(text):
    """Affiche un header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")


def check_python_version():
    """Vérifie la version de Python"""
    print("🐍 Version de Python")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 9:
        print("   ✅ Version compatible (≥3.9)")
        return True
    else:
        print("   ⚠️  Version recommandée : Python 3.9+")
        return False


def check_dependencies():
    """Vérifie les dépendances"""
    print("\n📦 Dépendances Python")

    deps = {
        "torch": "PyTorch",
        "torchvision": "TorchVision",
        "ultralytics": "YOLOv8",
        "cv2": "OpenCV",
        "PIL": "Pillow",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "matplotlib": "Matplotlib",
        "seaborn": "Seaborn",
        "datasets": "HuggingFace Datasets",
        "yaml": "PyYAML",
        "tqdm": "tqdm",
    }

    results = {}

    for module, name in deps.items():
        try:
            if module == "cv2":
                import cv2

                version = cv2.__version__
            elif module == "PIL":
                from PIL import Image

                version = Image.__version__ if hasattr(Image, "__version__") else "OK"
            elif module == "yaml":
                import yaml

                version = "OK"
            else:
                mod = __import__(module)
                version = mod.__version__ if hasattr(mod, "__version__") else "OK"

            print(f"   ✅ {name:25s} {version}")
            results[module] = True
        except ImportError:
            print(f"   ❌ {name:25s} Non installé")
            results[module] = False

    return all(results.values())


def check_gpu():
    """Vérifie la disponibilité du GPU"""
    print("\n🖥️  Matériel")

    try:
        import torch

        if torch.cuda.is_available():
            print(f"   ✅ CUDA disponible")
            print(f"      GPU : {torch.cuda.get_device_name(0)}")
            print(
                f"      Mémoire : {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
            )
            return "cuda"
        elif torch.backends.mps.is_available():
            print(f"   ✅ Apple Silicon (MPS) disponible")
            return "mps"
        else:
            print(f"   ⚠️  Pas de GPU détecté")
            print(f"      L'entraînement sera effectué sur CPU (plus lent)")
            return "cpu"
    except Exception as e:
        print(f"   ❌ Erreur lors de la détection : {e}")
        return None


def check_folders():
    """Vérifie la structure des dossiers"""
    print("\n📁 Structure des dossiers")

    base = Path(__file__).parent.parent

    folders = [
        "data",
        "data/raw",
        "data/processed",
        "data/annotations",
        "models",
        "scripts",
        "notebooks",
        "results",
        "results/images",
        "results/metrics",
        "logs",
    ]

    all_ok = True

    for folder in folders:
        path = base / folder
        if path.exists():
            print(f"   ✅ {folder}/")
        else:
            print(f"   ⚠️  {folder}/ (sera créé automatiquement)")
            all_ok = False

    return all_ok


def check_scripts():
    """Vérifie les scripts"""
    print("\n📜 Scripts disponibles")

    base = Path(__file__).parent.parent
    scripts_dir = base / "scripts"

    required_scripts = [
        "download_data.py",
        "prepare_dataset.py",
        "train.py",
        "validate.py",
        "inference.py",
    ]

    all_ok = True

    for script in required_scripts:
        path = scripts_dir / script
        if path.exists():
            print(f"   ✅ {script}")
        else:
            print(f"   ❌ {script} manquant")
            all_ok = False

    return all_ok


def check_disk_space():
    """Vérifie l'espace disque"""
    print("\n💾 Espace disque")

    try:
        import shutil

        base = Path(__file__).parent.parent
        total, used, free = shutil.disk_usage(base)

        free_gb = free / (1024**3)

        print(f"   Espace disponible : {free_gb:.2f} GB")

        if free_gb >= 10:
            print(f"   ✅ Espace suffisant (≥10 GB)")
            return True
        else:
            print(f"   ⚠️  Espace limité (recommandé : ≥10 GB)")
            print(f"      Nécessaire pour :")
            print(f"      - Dataset : ~3.5 GB")
            print(f"      - Modèles : ~2 GB")
            print(f"      - Résultats : ~2 GB")
            return False
    except Exception as e:
        print(f"   ⚠️  Impossible de vérifier : {e}")
        return None


def check_dataset():
    """Vérifie si le dataset est téléchargé"""
    print("\n📊 Dataset")

    base = Path(__file__).parent.parent
    raw_dir = base / "data" / "raw"
    processed_dir = base / "data" / "processed"

    raw_exists = raw_dir.exists() and (raw_dir / "train").exists()
    processed_exists = processed_dir.exists() and (processed_dir / "data.yaml").exists()

    if raw_exists:
        print(f"   ✅ Dataset brut téléchargé")
    else:
        print(f"   ⏳ Dataset brut non téléchargé")
        print(f"      Commande : python scripts/download_data.py")

    if processed_exists:
        print(f"   ✅ Dataset YOLO préparé")
    else:
        print(f"   ⏳ Dataset YOLO non préparé")
        if raw_exists:
            print(f"      Commande : python scripts/prepare_dataset.py")

    return raw_exists and processed_exists


def check_model():
    """Vérifie si un modèle est entraîné"""
    print("\n🤖 Modèle")

    base = Path(__file__).parent.parent
    final_model = base / "models" / "final" / "best_model.pt"

    if final_model.exists():
        size_mb = final_model.stat().st_size / (1024**2)
        print(f"   ✅ Modèle final disponible ({size_mb:.1f} MB)")
        return True
    else:
        print(f"   ⏳ Aucun modèle entraîné")
        print(f"      Commande : python scripts/train.py")
        return False


def print_next_steps(checks):
    """Affiche les prochaines étapes"""
    print_header("🚀 PROCHAINES ÉTAPES")

    if not checks["dependencies"]:
        print("1. ❌ Installer les dépendances manquantes")
        print("   pip install -r requirements.txt\n")
        return

    if not checks["dataset"]:
        print("1. 📥 Télécharger le dataset (30-60 min)")
        print("   python scripts/download_data.py")
        print()
        print("2. 🔧 Préparer le dataset pour YOLO (15-30 min)")
        print("   python scripts/prepare_dataset.py")
        print()

    if not checks["model"]:
        print("3. 🎯 Entraîner le modèle (2-8h)")
        print("   python scripts/train.py")
        print()
        print("4. ✅ Valider le modèle")
        print("   python scripts/validate.py")
        print()

    if checks["model"]:
        print("✅ Tout est prêt !")
        print()
        print("🎬 Tester en temps réel :")
        print("   python scripts/inference.py --source 0")
        print()


def main():
    """Fonction principale"""
    print_header("🔍 VÉRIFICATION DE L'ENVIRONNEMENT")
    print("Détection du Code Vestimentaire ENSITECH\n")

    checks = {
        "python": check_python_version(),
        "dependencies": check_dependencies(),
        "gpu": check_gpu() is not None,
        "folders": check_folders(),
        "scripts": check_scripts(),
        "disk": check_disk_space(),
        "dataset": check_dataset(),
        "model": check_model(),
    }

    # Résumé
    print_header("📋 RÉSUMÉ")

    total = len(checks)
    passed = sum(1 for v in checks.values() if v)

    print(f"Tests réussis : {passed}/{total}\n")

    for name, status in checks.items():
        emoji = "✅" if status else "⏳"
        print(f"{emoji} {name.capitalize()}")

    # Prochaines étapes
    print_next_steps(checks)

    # Conclusion
    if all(checks.values()):
        print_header("🎉 ENVIRONNEMENT OPÉRATIONNEL")
        print("Tout est prêt pour l'entraînement !")
    elif checks["dependencies"] and checks["scripts"]:
        print_header("⏳ CONFIGURATION PARTIELLE")
        print("L'environnement est configuré.")
        print("Suivez les prochaines étapes ci-dessus.")
    else:
        print_header("⚠️  CONFIGURATION INCOMPLÈTE")
        print("Veuillez résoudre les problèmes ci-dessus.")

    print()


if __name__ == "__main__":
    main()
