"""
Script pour préparer le dataset Fashionpedia COMPLET (46 catégories) au format YOLO
Mapping précis vers les catégories du code vestimentaire ENSITECH

Dataset : detection-datasets/fashionpedia (HuggingFace)
46 catégories fines au lieu de 4 catégories grossières

IMPORTANT : Ce script utilise le dataset COMPLET, pas fashionpedia_4_categories
"""

import json
import os
import shutil
from pathlib import Path

import yaml
from datasets import load_dataset
from PIL import Image
from tqdm import tqdm

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_ANNOTATIONS = BASE_DIR / "data" / "annotations"

# ============================================================================
# MAPPING DES CATÉGORIES FASHIONPEDIA (46 catégories) → ENSITECH
# ============================================================================
#
# Catégories Fashionpedia complètes :
#  0: shirt, blouse          1: top, t-shirt, sweatshirt   2: sweater
#  3: cardigan               4: jacket                     5: vest
#  6: pants                  7: shorts                     8: skirt
#  9: coat                  10: dress                     11: jumpsuit
# 12: cape                  13: glasses                   14: hat
# 15: headband/head covering 16: tie                      17: glove
# 18: watch                 19: belt                      20: leg warmer
# 21: tights, stockings     22: sock                      23: shoe
# 24: bag, wallet           25: scarf                     26: umbrella
# 27: hood                  28: collar                    29: lapel
# 30: epaulette             31: sleeve                    32: pocket
# 33: neckline              34: buckle                    35: zipper
# 36: applique              37: bead                      38: bow
# 39: flower                40: fringe                    41: ribbon
# 42: rivet                 43: ruffle                    44: sequin
# 45: tassel
#
# Règlement ENSITECH - Éléments interdits :
# - Bas : pantalon baggy, short, bermuda, jean troué, mini-jupe
# - Hauts : crop top, haut ouvert dans le dos, tenue de sport
# - Chaussures : tongs
# - Accessoires : casquette, chapeau, bonnet, bandana, tout couvre-chef
#
# STRATÉGIE :
# On ne mappe QUE les catégories qu'on peut identifier avec certitude
# comme potentiellement non-conformes. Les catégories ambiguës sont IGNORÉES.
# ============================================================================

CATEGORY_MAPPING = {
    # -------------------------------------------------------------------------
    # CATÉGORIE 0 : "short_bermuda" - Bas courts interdits
    # -------------------------------------------------------------------------
    # Fashionpedia ID 7 = "shorts"
    # Couvre : short, bermuda, short de sport
    # C'est une correspondance directe et fiable
    7: {
        "yolo_id": 0,
        "name": "short_bermuda",
        "description": "Short, bermuda, short de sport",
    },

    # -------------------------------------------------------------------------
    # CATÉGORIE 1 : "jupe_courte" - Mini-jupe interdite
    # -------------------------------------------------------------------------
    # Fashionpedia ID 8 = "skirt"
    # NOTE : Le dataset ne distingue pas mini-jupe vs jupe longue.
    # On détecte toutes les jupes, et on pourrait affiner plus tard
    # avec un classificateur de longueur ou un seuil sur la bbox height.
    8: {
        "yolo_id": 1,
        "name": "jupe_courte",
        "description": "Jupe (potentiellement mini-jupe)",
    },

    # -------------------------------------------------------------------------
    # CATÉGORIE 2 : "couvre_chef" - Tous les couvre-chefs interdits
    # -------------------------------------------------------------------------
    # Fashionpedia ID 14 = "hat" -> casquette, chapeau, bonnet
    # Fashionpedia ID 15 = "headband, head covering, hair accessory" -> bandana, etc.
    # Correspondance directe et très fiable
    14: {
        "yolo_id": 2,
        "name": "couvre_chef",
        "description": "Casquette, chapeau, bonnet",
    },
    15: {
        "yolo_id": 2,
        "name": "couvre_chef",
        "description": "Bandana, couvre-chef, accessoire tête",
    },

    # -------------------------------------------------------------------------
    # CATÉGORIES IGNORÉES (non mappées) - et pourquoi :
    # -------------------------------------------------------------------------
    # - ID 23 (shoe) : Contient TOUTES les chaussures. On ne peut pas
    #   distinguer les tongs des baskets. → IGNORÉ
    # - ID 1 (top, t-shirt) : Contient tous les hauts. On ne peut pas
    #   distinguer un crop top d'un t-shirt normal. → IGNORÉ
    # - ID 6 (pants) : Contient tous les pantalons. On ne peut pas
    #   distinguer un baggy d'un pantalon normal ni un jean troué. → IGNORÉ
    # - ID 21 (tights, stockings) : Leggings inclus mais aussi collants
    #   normaux. Trop ambigu. → IGNORÉ
    # - Toutes les parties de vêtements (sleeve, collar, pocket, etc.)
    #   ne sont pas pertinentes pour la détection de code vestimentaire.
    # -------------------------------------------------------------------------
}

# Classes finales pour YOLO (uniquement les catégories détectables)
YOLO_CLASSES = {
    0: "short_bermuda",
    1: "jupe_courte",
    2: "couvre_chef",
}

# Nombre de classes
NUM_CLASSES = len(YOLO_CLASSES)


def create_yolo_structure():
    """
    Crée la structure de dossiers pour YOLO
    """
    print("\n📁 Création de la structure YOLO...")

    for split in ["train", "val", "test"]:
        images_dir = DATA_PROCESSED / split / "images"
        labels_dir = DATA_PROCESSED / split / "labels"
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

    print("✅ Structure créée")


def convert_bbox_to_yolo(bbox, img_width, img_height):
    """
    Convertit les bounding boxes du format Pascal VOC [x_min, y_min, x_max, y_max]
    au format YOLO [x_center, y_center, width, height] normalisé entre 0 et 1

    Args:
        bbox: [x_min, y_min, x_max, y_max]
        img_width: Largeur de l'image
        img_height: Hauteur de l'image

    Returns:
        [x_center, y_center, width, height] normalisé, ou None si invalide
    """
    x_min, y_min, x_max, y_max = bbox

    # Vérifications de base
    if x_max <= x_min or y_max <= y_min:
        return None
    if img_width <= 0 or img_height <= 0:
        return None

    # Clamp les valeurs aux limites de l'image
    x_min = max(0, min(x_min, img_width))
    y_min = max(0, min(y_min, img_height))
    x_max = max(0, min(x_max, img_width))
    y_max = max(0, min(y_max, img_height))

    # Calculer le centre et les dimensions
    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    width = x_max - x_min
    height = y_max - y_min

    # Filtrer les bboxes trop petites (bruit d'annotation)
    if width < 5 or height < 5:
        return None

    # Normaliser
    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    width_norm = width / img_width
    height_norm = height / img_height

    # Vérification finale
    if all(0 <= v <= 1 for v in [x_center_norm, y_center_norm, width_norm, height_norm]):
        return [x_center_norm, y_center_norm, width_norm, height_norm]

    return None


def process_split(split_name, dataset_split, yolo_split_name):
    """
    Traite un split du dataset (train, val)

    Args:
        split_name: Nom du split original ('train', 'val')
        dataset_split: Dataset HuggingFace
        yolo_split_name: Nom du split pour YOLO ('train', 'val', 'test')
    """
    print(f"\n📊 Traitement du split '{split_name}' -> '{yolo_split_name}'")

    images_dir = DATA_PROCESSED / yolo_split_name / "images"
    labels_dir = DATA_PROCESSED / yolo_split_name / "labels"

    stats = {
        "total_images": 0,
        "images_with_violations": 0,
        "images_without_violations": 0,
        "total_violations": 0,
        "violations_per_category": {name: 0 for name in YOLO_CLASSES.values()},
        "skipped_categories": {},
    }

    for idx in tqdm(range(len(dataset_split)), desc=f"Processing {split_name}"):
        try:
            sample = dataset_split[idx]

            image_id = sample.get("image_id", idx)
            width = sample["width"]
            height = sample["height"]
            image = sample["image"]

            # Nom du fichier
            image_filename = f"{image_id:06d}.jpg"
            label_filename = f"{image_id:06d}.txt"

            # Traiter les annotations AVANT de sauvegarder l'image
            # (pour ne sauvegarder que les images avec des objets pertinents
            # ou un échantillon d'images sans violations pour les négatifs)
            objects = sample.get("objects", {})
            categories = objects.get("category", [])
            bboxes = objects.get("bbox", [])

            # Filtrer et convertir les annotations
            yolo_annotations = []

            for category, bbox in zip(categories, bboxes):
                # Vérifier si cette catégorie est mappée
                mapped = CATEGORY_MAPPING.get(category)

                if mapped is None:
                    # Catégorie non pertinente → on ignore silencieusement
                    continue

                yolo_class_id = mapped["yolo_id"]

                # Convertir la bbox au format YOLO
                yolo_bbox = convert_bbox_to_yolo(bbox, width, height)

                if yolo_bbox is not None:
                    yolo_annotations.append([yolo_class_id] + yolo_bbox)
                    stats["total_violations"] += 1
                    stats["violations_per_category"][YOLO_CLASSES[yolo_class_id]] += 1

            # Sauvegarder l'image
            image_path = images_dir / image_filename
            if isinstance(image, Image.Image):
                image.save(image_path, "JPEG", quality=95)
            else:
                Image.fromarray(image).save(image_path, "JPEG", quality=95)

            # Sauvegarder les annotations YOLO
            # (fichier vide = image sans violation = exemple négatif)
            label_path = labels_dir / label_filename
            with open(label_path, "w") as f:
                for ann in yolo_annotations:
                    f.write(
                        f"{ann[0]} {ann[1]:.6f} {ann[2]:.6f} {ann[3]:.6f} {ann[4]:.6f}\n"
                    )

            stats["total_images"] += 1
            if len(yolo_annotations) > 0:
                stats["images_with_violations"] += 1
            else:
                stats["images_without_violations"] += 1

        except Exception as e:
            print(f"\n⚠️  Erreur sur l'image {idx}: {e}")
            continue

    # Afficher les statistiques
    print(f"\n📈 Statistiques pour '{yolo_split_name}':")
    print(f"  - Images totales : {stats['total_images']}")
    print(f"  - Images avec violations : {stats['images_with_violations']}")
    print(f"  - Images sans violations (négatifs) : {stats['images_without_violations']}")
    print(f"  - Objets interdits détectés : {stats['total_violations']}")
    print(f"  - Répartition par catégorie :")
    for cat_name, count in stats["violations_per_category"].items():
        print(f"    • {cat_name}: {count}")

    return stats


def create_yaml_config(all_stats):
    """
    Crée le fichier de configuration YAML pour YOLO
    """
    print("\n📝 Création du fichier de configuration YOLO...")

    yaml_config = {
        "path": str(DATA_PROCESSED.absolute()),
        "train": "train/images",
        "val": "val/images",
        "nc": NUM_CLASSES,
        "names": list(YOLO_CLASSES.values()),
    }

    yaml_path = DATA_PROCESSED / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_config, f, default_flow_style=False, allow_unicode=True)

    print(f"✅ Configuration YOLO sauvegardée : {yaml_path}")
    print(f"\n📋 Contenu du data.yaml :")
    print(f"   Classes ({NUM_CLASSES}) :")
    for i, name in YOLO_CLASSES.items():
        print(f"     {i}: {name}")

    # Sauvegarder les statistiques
    stats_path = DATA_PROCESSED / "statistics.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Statistiques sauvegardées : {stats_path}")

    return yaml_path


def main():
    """
    Fonction principale
    """
    print("=" * 60)
    print("PRÉPARATION DU DATASET FASHIONPEDIA COMPLET")
    print("Mapping vers le code vestimentaire ENSITECH")
    print("=" * 60)

    # Créer la structure YOLO
    create_yolo_structure()

    # Afficher le mapping
    print("\n🏷️  Mapping des catégories Fashionpedia → ENSITECH :")
    print("-" * 50)
    mapped_ids = set()
    for fashionpedia_id, mapping in CATEGORY_MAPPING.items():
        yolo_id = mapping["yolo_id"]
        print(f"  Fashionpedia [{fashionpedia_id:2d}] → YOLO [{yolo_id}] : {mapping['name']}")
        print(f"      Description : {mapping['description']}")
        mapped_ids.add(fashionpedia_id)

    print(f"\n  ℹ️  {46 - len(mapped_ids)} catégories Fashionpedia ignorées (non pertinentes)")
    print(f"  ℹ️  Les images sans objets interdits servent d'exemples négatifs")

    # Charger le dataset depuis HuggingFace
    print("\n📥 Chargement du dataset Fashionpedia complet depuis HuggingFace...")
    print("   (Cela peut prendre plusieurs minutes lors du premier téléchargement)")

    dataset = load_dataset("detection-datasets/fashionpedia")

    print(f"\n✅ Dataset chargé !")
    print(f"   Splits disponibles : {list(dataset.keys())}")
    for split_name in dataset:
        print(f"   - {split_name}: {len(dataset[split_name])} images")

    # Traiter chaque split
    all_stats = {}

    # Train
    if "train" in dataset:
        stats = process_split("train", dataset["train"], "train")
        all_stats["train"] = stats

    # Validation
    if "val" in dataset:
        stats = process_split("val", dataset["val"], "val")
        all_stats["val"] = stats
    elif "validation" in dataset:
        stats = process_split("validation", dataset["validation"], "val")
        all_stats["val"] = stats

    # Créer le fichier de configuration YOLO
    yaml_path = create_yaml_config(all_stats)

    # Résumé final
    print("\n" + "=" * 60)
    print("✅ PRÉPARATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 60)

    total_violations = sum(s.get("total_violations", 0) for s in all_stats.values())
    total_images = sum(s.get("total_images", 0) for s in all_stats.values())
    total_with_violations = sum(s.get("images_with_violations", 0) for s in all_stats.values())

    print(f"\n📊 Résumé global :")
    print(f"   Images totales : {total_images}")
    print(f"   Images avec violations : {total_with_violations}")
    print(f"   Images sans violations (négatifs) : {total_images - total_with_violations}")
    print(f"   Objets interdits annotés : {total_violations}")
    print(f"\n📂 Dataset YOLO prêt dans : {DATA_PROCESSED}")
    print(f"📝 Configuration YOLO : {yaml_path}")
    print(f"\n📌 Prochaine étape : python scripts/train.py")
    print(f"\n⚠️  LIMITATIONS CONNUES :")
    print(f"   - Les tongs ne peuvent pas être distinguées des autres chaussures")
    print(f"   - Les crop tops ne peuvent pas être distingués des hauts normaux")
    print(f"   - Les jeans troués / pantalons baggy ne sont pas détectables")
    print(f"   - Les jupes longues seront aussi détectées (pas seulement mini-jupes)")
    print(f"   → Pour ces cas, envisager un dataset complémentaire (Roboflow, CVAT)")


if __name__ == "__main__":
    main()