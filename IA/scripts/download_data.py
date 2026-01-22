"""
Script pour télécharger le dataset Fashionpedia depuis HuggingFace
"""

import json
import os
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_fashionpedia():
    """
    Télécharge le dataset Fashionpedia 4 catégories depuis HuggingFace
    """
    print("=" * 60)
    print("Téléchargement du dataset Fashionpedia")
    print("=" * 60)

    try:
        # Téléchargement du dataset
        print("\n📥 Chargement depuis HuggingFace...")
        dataset = load_dataset("detection-datasets/fashionpedia_4_categories")

        # Affichage des informations
        print("\n✅ Dataset chargé avec succès !")
        print(f"\n📊 Statistiques du dataset :")
        print(f"  Splits disponibles : {list(dataset.keys())}")
        print(f"  - Train : {len(dataset['train'])} images")

        # Le dataset utilise 'val' au lieu de 'validation'
        val_key = "val" if "val" in dataset else "validation"
        test_key = "test" if "test" in dataset else None

        if val_key in dataset:
            print(f"  - Validation : {len(dataset[val_key])} images")
        if test_key and test_key in dataset:
            print(f"  - Test : {len(dataset[test_key])} images")

        total = len(dataset["train"])
        if val_key in dataset:
            total += len(dataset[val_key])
        if test_key and test_key in dataset:
            total += len(dataset[test_key])
        print(f"  - Total : {total} images")

        # Catégories
        print(f"\n🏷️  Catégories détectées :")
        categories = {
            0: "Accessories (Accessoires)",
            1: "Bags (Sacs)",
            2: "Clothing (Vêtements)",
            3: "Shoes (Chaussures)",
        }
        for cat_id, cat_name in categories.items():
            print(f"  - {cat_id}: {cat_name}")

        # Sauvegarde des métadonnées
        metadata = {
            "dataset_name": "fashionpedia_4_categories",
            "source": "huggingface",
            "splits": {
                "train": len(dataset["train"]),
            },
            "categories": categories,
            "total_images": len(dataset["train"]),
        }

        # Ajouter val et test s'ils existent
        if val_key in dataset:
            metadata["splits"][val_key] = len(dataset[val_key])
            metadata["total_images"] += len(dataset[val_key])
        if test_key and test_key in dataset:
            metadata["splits"][test_key] = len(dataset[test_key])
            metadata["total_images"] += len(dataset[test_key])

        metadata_path = DATA_DIR / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        print(f"\n💾 Métadonnées sauvegardées dans : {metadata_path}")

        # Sauvegarde du dataset
        print(f"\n💾 Sauvegarde du dataset dans : {DATA_DIR}")

        # Sauvegarder chaque split disponible
        for split_name in dataset.keys():
            split_path = DATA_DIR / split_name
            split_path.mkdir(exist_ok=True)

            print(f"\n  Sauvegarde de '{split_name}'...")
            dataset[split_name].save_to_disk(str(split_path))

        print("\n" + "=" * 60)
        print("✅ Téléchargement terminé avec succès !")
        print("=" * 60)
        print(f"\nProchaine étape : python scripts/prepare_dataset.py")

        return dataset

    except Exception as e:
        print(f"\n❌ Erreur lors du téléchargement : {e}")
        raise


def inspect_sample():
    """
    Inspecte un échantillon du dataset pour comprendre la structure
    """
    print("\n" + "=" * 60)
    print("Inspection d'un échantillon")
    print("=" * 60)

    try:
        dataset = load_dataset("detection-datasets/fashionpedia_4_categories")
        sample = dataset["train"][0]

        print(f"\n📝 Structure d'un exemple :")
        print(f"  - image_id : {sample.get('image_id', 'N/A')}")
        print(f"  - width : {sample.get('width', 'N/A')} px")
        print(f"  - height : {sample.get('height', 'N/A')} px")

        if "objects" in sample:
            objects = sample["objects"]
            print(f"  - Nombre d'objets : {len(objects.get('bbox_id', []))}")

            if len(objects.get("bbox_id", [])) > 0:
                print(f"\n  Premier objet détecté :")
                print(f"    - bbox_id : {objects['bbox_id'][0]}")
                print(f"    - category : {objects['category'][0]}")
                print(f"    - bbox : {objects['bbox'][0]}")
                print(f"    - area : {objects['area'][0]}")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Erreur lors de l'inspection : {e}")


if __name__ == "__main__":
    # Inspecter d'abord un échantillon
    inspect_sample()

    # Télécharger le dataset complet
    dataset = download_fashionpedia()

    print("\n📌 Le dataset est prêt à être traité !")
    print(f"📂 Emplacement : {DATA_DIR}")
