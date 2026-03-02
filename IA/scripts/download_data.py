"""
Télécharge les deux datasets nécessaires :
- Fashionpedia complet (46 catégories, avec bounding boxes officiels)
- iMaterialist filtré en streaming (crop tops, baggy jeans, tenue sport)
"""

import json
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

# Catégories à extraire de iMaterialist (celles manquantes dans Fashionpedia)
IMATERIALIST_TARGET_CATEGORIES = [
    "Crop Tops",
    "Baggy Jeans",
    "Leggings",
    "Athletic Pants",
    "Athletic Sets",
]

# Nombre max d'images par catégorie depuis iMaterialist
MAX_PER_CATEGORY = 3000


def download_fashionpedia():
    """
    Télécharge le dataset Fashionpedia complet (46 catégories)
    depuis detection-datasets/fashionpedia sur HuggingFace.
    """
    print("\n" + "=" * 60)
    print("TÉLÉCHARGEMENT DE FASHIONPEDIA (complet)")
    print("=" * 60)

    print("\n📥 Chargement depuis HuggingFace...")
    dataset = load_dataset("detection-datasets/fashionpedia")

    print("\n✅ Fashionpedia chargé")
    print(f"📊 Splits disponibles : {list(dataset.keys())}")
    for split_name in dataset.keys():
        print(f"  - {split_name} : {len(dataset[split_name])} images")

    # Sauvegarde
    save_dir = DATA_DIR / "fashionpedia"
    print(f"\n💾 Sauvegarde dans : {save_dir}")
    for split_name in dataset.keys():
        split_path = save_dir / split_name
        split_path.mkdir(parents=True, exist_ok=True)
        print(f"  Sauvegarde de '{split_name}'...")
        dataset[split_name].save_to_disk(str(split_path))

    print("✅ Fashionpedia sauvegardé")


def download_imaterialist():
    """
    Télécharge iMaterialist en mode streaming pour éviter de charger
    les 721k images en mémoire. On filtre uniquement les catégories
    nécessaires et on sauvegarde max MAX_PER_CATEGORY images par catégorie.
    """
    print("\n" + "=" * 60)
    print("TÉLÉCHARGEMENT DE iMaterialist (filtré)")
    print("=" * 60)

    print(f"\n🎯 Catégories cibles : {IMATERIALIST_TARGET_CATEGORIES}")
    print(f"📏 Max {MAX_PER_CATEGORY} images par catégorie")

    save_dir = DATA_DIR / "imaterialist"
    total_target = MAX_PER_CATEGORY * len(IMATERIALIST_TARGET_CATEGORIES)

    # Compteur par catégorie
    collected = {cat: 0 for cat in IMATERIALIST_TARGET_CATEGORIES}

    print("\n📥 Streaming depuis HuggingFace...")
    dataset = load_dataset("Marqo/iMaterialist", streaming=True)

    # Détecter le nom du split disponible
    split_name = list(dataset.keys())[0]
    print(f"  Split détecté : '{split_name}'")
    stream = dataset[split_name]

    total_collected = 0
    for sample in stream:
        category = sample.get("category")

        # Ignorer si pas une catégorie cible ou si on a atteint le max
        if category not in IMATERIALIST_TARGET_CATEGORIES:
            continue
        if collected[category] >= MAX_PER_CATEGORY:
            # Vérifier si toutes les catégories sont pleines
            if all(c >= MAX_PER_CATEGORY for c in collected.values()):
                break
            continue

        # Créer le dossier pour cette catégorie
        cat_dir = save_dir / category.replace(" ", "_")
        cat_dir.mkdir(parents=True, exist_ok=True)

        # Sauvegarder l'image
        idx = collected[category]
        sample["image"].save(str(cat_dir / f"{idx:06d}.jpg"), "JPEG")

        collected[category] += 1
        total_collected += 1

        # Afficher la progression toutes les 500 images
        if total_collected % 500 == 0:
            status = ", ".join(f"{k}: {v}" for k, v in collected.items())
            print(f"  [{total_collected}/{total_target}] {status}")

    # Résumé final
    print(f"\n📊 Images collectées :")
    for cat, count in collected.items():
        print(f"  • {cat}: {count}")
    print(f"  • Total: {total_collected}")

    # Sauvegarder le résumé
    with open(save_dir / "summary.json", "w") as f:
        json.dump(collected, f, indent=2)

    print("✅ iMaterialist filtré et sauvegardé")


def main():
    print("=" * 60)
    print("TÉLÉCHARGEMENT DES DATASETS")
    print("Détection du Code Vestimentaire ENSITECH")
    print("=" * 60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fashionpedia complet (avec bounding boxes)
    download_fashionpedia()

    # 2. iMaterialist filtré (catégories manquantes)
    download_imaterialist()

    print("\n" + "=" * 60)
    print("✅ TOUS LES DATASETS TÉLÉCHARGÉS")
    print("=" * 60)
    print(f"\n📂 Données sauvegardées dans : {DATA_DIR}")
    print(f"📌 Prochaine étape : python scripts/prepare_dataset.py")


if __name__ == "__main__":
    main()
