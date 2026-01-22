"""
Script pour préparer le dataset au format YOLO
Conversion des annotations et mapping vers les catégories du code vestimentaire
"""

import json
import os
import shutil
from pathlib import Path

import yaml
from datasets import load_from_disk
from PIL import Image
from tqdm import tqdm

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_ANNOTATIONS = BASE_DIR / "data" / "annotations"

# Mapping des catégories Fashionpedia vers le code vestimentaire ENSITECH
# Pour cette première version, nous utiliserons les catégories générales
# Vous pourrez affiner plus tard avec des sous-catégories spécifiques

CATEGORY_MAPPING = {
    # Fashionpedia -> ENSITECH Code Vestimentaire
    0: {  # Accessories -> Accessoires interdits (casquettes, chapeaux, bonnets, etc.)
        "id": 0,
        "name": "accessoire_interdit",
        "description": "Casquette, chapeau, bonnet, bandana, couvre-chef",
    },
    1: {  # Bags -> Non concerné par le code vestimentaire (on peut l'ignorer)
        "id": None,  # Ignorer cette catégorie
        "name": "sac",
        "description": "Sac (non concerné par le règlement)",
    },
    2: {  # Clothing -> Vêtements (à subdiviser plus tard)
        "id": 1,
        "name": "vetement_interdit",
        "description": "Crop top, dos ouvert, tenue sport, short, bermuda, mini-jupe, baggy, jean troué",
    },
    3: {  # Shoes -> Chaussures interdites (tongs)
        "id": 2,
        "name": "chaussure_interdite",
        "description": "Tongs",
    },
}

# Classes finales pour YOLO (uniquement les catégories pertinentes)
YOLO_CLASSES = {
    0: "accessoire_interdit",
    1: "vetement_interdit",
    2: "chaussure_interdite",
}


def create_yolo_structure():
    """
    Crée la structure de dossiers pour YOLO
    """
    print("\n📁 Création de la structure YOLO...")

    # Structure YOLO
    for split in ["train", "val", "test"]:
        images_dir = DATA_PROCESSED / split / "images"
        labels_dir = DATA_PROCESSED / split / "labels"
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

    print("✅ Structure créée")


def convert_bbox_to_yolo(bbox, img_width, img_height):
    """
    Convertit les bounding boxes du format [x_min, y_min, x_max, y_max] au format YOLO
    Format YOLO : [x_center, y_center, width, height] normalisé entre 0 et 1

    Args:
        bbox: [x_min, y_min, x_max, y_max]
        img_width: Largeur de l'image
        img_height: Hauteur de l'image

    Returns:
        [x_center, y_center, width, height] normalisé
    """
    x_min, y_min, x_max, y_max = bbox

    # Calculer le centre et les dimensions
    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    width = x_max - x_min
    height = y_max - y_min

    # Normaliser
    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    width_norm = width / img_width
    height_norm = height / img_height

    return [x_center_norm, y_center_norm, width_norm, height_norm]


def process_split(split_name, dataset_split):
    """
    Traite un split du dataset (train, val, test)

    Args:
        split_name: Nom du split ('train', 'validation', 'test')
        dataset_split: Dataset HuggingFace
    """
    # Mapper 'validation' vers 'val' pour YOLO
    yolo_split_name = "val" if split_name == "validation" else split_name

    print(f"\n📊 Traitement du split '{split_name}' -> '{yolo_split_name}'")

    images_dir = DATA_PROCESSED / yolo_split_name / "images"
    labels_dir = DATA_PROCESSED / yolo_split_name / "labels"

    stats = {
        "total_images": 0,
        "images_with_relevant_objects": 0,
        "total_objects": 0,
        "objects_per_category": {name: 0 for name in YOLO_CLASSES.values()},
    }

    for idx, sample in enumerate(tqdm(dataset_split, desc=f"Processing {split_name}")):
        try:
            image_id = sample.get("image_id", idx)
            width = sample["width"]
            height = sample["height"]
            image = sample["image"]

            # Nom du fichier
            image_filename = f"{image_id:06d}.jpg"
            label_filename = f"{image_id:06d}.txt"

            # Sauvegarder l'image
            image_path = images_dir / image_filename
            if isinstance(image, Image.Image):
                image.save(image_path, "JPEG")
            else:
                # Si c'est déjà un array numpy
                Image.fromarray(image).save(image_path, "JPEG")

            # Traiter les annotations
            objects = sample.get("objects", {})
            categories = objects.get("category", [])
            bboxes = objects.get("bbox", [])

            # Filtrer et convertir les annotations
            yolo_annotations = []

            for category, bbox in zip(categories, bboxes):
                # Mapper la catégorie
                mapped_cat = CATEGORY_MAPPING.get(category, {})
                yolo_class_id = mapped_cat.get("id")

                # Ignorer si la catégorie n'est pas pertinente (comme les sacs)
                if yolo_class_id is None:
                    continue

                # Convertir la bbox au format YOLO
                yolo_bbox = convert_bbox_to_yolo(bbox, width, height)

                # Vérifier que les valeurs sont valides
                if all(0 <= v <= 1 for v in yolo_bbox):
                    yolo_annotations.append([yolo_class_id] + yolo_bbox)
                    stats["total_objects"] += 1
                    stats["objects_per_category"][YOLO_CLASSES[yolo_class_id]] += 1

            # Sauvegarder les annotations YOLO
            label_path = labels_dir / label_filename
            with open(label_path, "w") as f:
                for ann in yolo_annotations:
                    # Format: class_id x_center y_center width height
                    f.write(
                        f"{ann[0]} {ann[1]:.6f} {ann[2]:.6f} {ann[3]:.6f} {ann[4]:.6f}\n"
                    )

            stats["total_images"] += 1
            if len(yolo_annotations) > 0:
                stats["images_with_relevant_objects"] += 1

        except Exception as e:
            print(f"\n⚠️  Erreur sur l'image {image_id}: {e}")
            continue

    # Afficher les statistiques
    print(f"\n📈 Statistiques pour '{yolo_split_name}':")
    print(f"  - Images totales : {stats['total_images']}")
    print(
        f"  - Images avec objets pertinents : {stats['images_with_relevant_objects']}"
    )
    print(f"  - Objets totaux : {stats['total_objects']}")
    print(f"  - Répartition par catégorie :")
    for cat_name, count in stats["objects_per_category"].items():
        print(f"    • {cat_name}: {count}")

    return stats


def create_yaml_config(all_stats):
    """
    Crée le fichier de configuration YAML pour YOLO

    Args:
        all_stats: Dictionnaire des statistiques pour tous les splits
    """
    print("\n📝 Création du fichier de configuration YOLO...")

    yaml_config = {
        "path": str(DATA_PROCESSED.absolute()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(YOLO_CLASSES),
        "names": list(YOLO_CLASSES.values()),
    }

    yaml_path = DATA_PROCESSED / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_config, f, default_flow_style=False, allow_unicode=True)

    print(f"✅ Configuration sauvegardée : {yaml_path}")

    # Sauvegarder également les statistiques
    stats_path = DATA_PROCESSED / "statistics.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=4, ensure_ascii=False)

    print(f"✅ Statistiques sauvegardées : {stats_path}")

    return yaml_path


def main():
    """
    Fonction principale
    """
    print("=" * 60)
    print("PRÉPARATION DU DATASET POUR YOLO")
    print("=" * 60)

    # Vérifier que le dataset brut existe
    if not DATA_RAW.exists():
        print("\n❌ Dataset brut non trouvé !")
        print("Veuillez d'abord exécuter : python scripts/download_data.py")
        return

    # Créer la structure YOLO
    create_yolo_structure()

    # Afficher le mapping des catégories
    print("\n🏷️  Mapping des catégories :")
    for old_id, mapping in CATEGORY_MAPPING.items():
        if mapping["id"] is not None:
            print(f"  {old_id} -> {mapping['id']}: {mapping['name']}")
            print(f"      ({mapping['description']})")
        else:
            print(f"  {old_id} -> IGNORÉ: {mapping['name']}")

    # Charger et traiter chaque split
    all_stats = {}

    # Le dataset brut peut avoir "val" ou "validation"
    splits_to_process = [
        ("train", "train"),
        ("val", "val"),  # Essayer d'abord "val"
        ("validation", "val"),  # Si "val" n'existe pas, essayer "validation"
        ("test", "test"),
    ]

    processed_splits = set()
    for raw_split_name, yolo_split_name in splits_to_process:
        if yolo_split_name in processed_splits:
            continue  # Déjà traité

        split_path = DATA_RAW / raw_split_name

        if not split_path.exists():
            continue

        print(f"\n📂 Chargement du split '{raw_split_name}'...")
        dataset_split = load_from_disk(str(split_path))

        # Utiliser le nom YOLO pour le traitement
        stats = process_split(raw_split_name, dataset_split)
        all_stats[yolo_split_name] = stats
        processed_splits.add(yolo_split_name)

    # Créer le fichier de configuration YOLO
    yaml_path = create_yaml_config(all_stats)

    print("\n" + "=" * 60)
    print("✅ PRÉPARATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 60)
    print(f"\n📂 Dataset YOLO prêt dans : {DATA_PROCESSED}")
    print(f"📝 Configuration YOLO : {yaml_path}")
    print(f"\n📌 Prochaine étape : python scripts/train.py")


if __name__ == "__main__":
    main()
