"""
Script de validation du modèle entraîné
"""

import json
from datetime import datetime
from pathlib import Path

import yaml
from ultralytics import YOLO

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"


def load_model():
    """
    Charge le meilleur modèle entraîné
    """
    # Chercher le meilleur modèle
    final_model = MODELS_DIR / "final" / "best_model.pt"

    if final_model.exists():
        print(f"✅ Chargement du modèle : {final_model}")
        return YOLO(str(final_model))

    # Chercher dans les dossiers d'entraînement
    model_dirs = list(MODELS_DIR.glob("dress_code_detection_*"))

    if not model_dirs:
        raise FileNotFoundError(
            "❌ Aucun modèle trouvé.\n"
            "Veuillez d'abord entraîner un modèle : python scripts/train.py"
        )

    # Prendre le plus récent
    latest_dir = max(model_dirs, key=lambda p: p.stat().st_mtime)
    best_model = latest_dir / "weights" / "best.pt"

    if not best_model.exists():
        raise FileNotFoundError(f"❌ Modèle non trouvé dans {latest_dir}")

    print(f"✅ Chargement du modèle : {best_model}")
    return YOLO(str(best_model))


def validate_model(model):
    """
    Valide le modèle sur l'ensemble de validation
    """
    yaml_path = DATA_PROCESSED / "data.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError(f"❌ Configuration non trouvée : {yaml_path}")

    print("\n" + "=" * 60)
    print("VALIDATION DU MODÈLE")
    print("=" * 60)

    print("\n🔍 Évaluation sur l'ensemble de validation...")

    # Valider
    results = model.val(data=str(yaml_path), split="val")

    # Extraire les métriques
    metrics = {
        "mAP50": float(results.box.map50) if hasattr(results.box, "map50") else None,
        "mAP50-95": float(results.box.map) if hasattr(results.box, "map") else None,
        "precision": float(results.box.mp) if hasattr(results.box, "mp") else None,
        "recall": float(results.box.mr) if hasattr(results.box, "mr") else None,
        "f1_score": None,
    }

    # Calculer F1-score
    if metrics["precision"] and metrics["recall"]:
        p = metrics["precision"]
        r = metrics["recall"]
        metrics["f1_score"] = 2 * (p * r) / (p + r) if (p + r) > 0 else 0

    # Afficher les résultats
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DE LA VALIDATION")
    print("=" * 60)

    print(f"\n🎯 Métriques globales :")
    print(
        f"   mAP@0.5      : {metrics['mAP50']:.4f}"
        if metrics["mAP50"]
        else "   mAP@0.5      : N/A"
    )
    print(
        f"   mAP@0.5:0.95 : {metrics['mAP50-95']:.4f}"
        if metrics["mAP50-95"]
        else "   mAP@0.5:0.95 : N/A"
    )
    print(
        f"   Precision    : {metrics['precision']:.4f}"
        if metrics["precision"]
        else "   Precision    : N/A"
    )
    print(
        f"   Recall       : {metrics['recall']:.4f}"
        if metrics["recall"]
        else "   Recall       : N/A"
    )
    print(
        f"   F1-Score     : {metrics['f1_score']:.4f}"
        if metrics["f1_score"]
        else "   F1-Score     : N/A"
    )

    # Métriques par classe
    if hasattr(results.box, "ap_class_index") and hasattr(results.box, "ap50"):
        print(f"\n📈 Métriques par classe :")

        with open(yaml_path, "r") as f:
            data_config = yaml.safe_load(f)

        class_names = data_config["names"]

        for idx, ap50 in zip(results.box.ap_class_index, results.box.ap50):
            class_name = class_names[int(idx)]
            print(f"   {class_name:25s} : {ap50:.4f}")

    # Évaluation par rapport aux objectifs
    print("\n" + "=" * 60)
    print("🎯 ÉVALUATION PAR RAPPORT AUX OBJECTIFS")
    print("=" * 60)

    target_precision = 0.90
    target_time = 2.0  # secondes

    if metrics["precision"]:
        if metrics["precision"] >= target_precision:
            print(
                f"✅ Précision : {metrics['precision']:.2%} (Objectif : ≥{target_precision:.0%})"
            )
        else:
            print(
                f"⚠️  Précision : {metrics['precision']:.2%} (Objectif : ≥{target_precision:.0%})"
            )
            print(
                f"   Amélioration nécessaire : {(target_precision - metrics['precision']):.2%}"
            )

    print(f"ℹ️  Temps d'inférence : À tester avec inference.py")

    # Sauvegarder les résultats
    results_file = (
        RESULTS_DIR
        / "metrics"
        / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(metrics, f, indent=4)

    print(f"\n💾 Résultats sauvegardés : {results_file}")

    return metrics


def test_model(model):
    """
    Teste le modèle sur l'ensemble de test
    """
    yaml_path = DATA_PROCESSED / "data.yaml"

    print("\n" + "=" * 60)
    print("TEST DU MODÈLE")
    print("=" * 60)

    print("\n🔍 Évaluation sur l'ensemble de test...")

    # Tester
    results = model.val(data=str(yaml_path), split="test")

    # Extraire les métriques
    metrics = {
        "mAP50": float(results.box.map50) if hasattr(results.box, "map50") else None,
        "mAP50-95": float(results.box.map) if hasattr(results.box, "map") else None,
        "precision": float(results.box.mp) if hasattr(results.box, "mp") else None,
        "recall": float(results.box.mr) if hasattr(results.box, "mr") else None,
    }

    print("\n📊 Résultats sur le test set :")
    print(
        f"   mAP@0.5      : {metrics['mAP50']:.4f}"
        if metrics["mAP50"]
        else "   mAP@0.5      : N/A"
    )
    print(
        f"   mAP@0.5:0.95 : {metrics['mAP50-95']:.4f}"
        if metrics["mAP50-95"]
        else "   mAP@0.5:0.95 : N/A"
    )
    print(
        f"   Precision    : {metrics['precision']:.4f}"
        if metrics["precision"]
        else "   Precision    : N/A"
    )
    print(
        f"   Recall       : {metrics['recall']:.4f}"
        if metrics["recall"]
        else "   Recall       : N/A"
    )

    # Sauvegarder les résultats
    results_file = (
        RESULTS_DIR
        / "metrics"
        / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(metrics, f, indent=4)

    print(f"\n💾 Résultats sauvegardés : {results_file}")

    return metrics


def main():
    """
    Fonction principale
    """
    print("=" * 60)
    print("VALIDATION DU MODÈLE YOLO")
    print("Détection du Code Vestimentaire ENSITECH")
    print("=" * 60)

    try:
        # Charger le modèle
        model = load_model()

        # Valider sur le validation set
        val_metrics = validate_model(model)

        # Tester sur le test set
        test_metrics = test_model(model)

        print("\n" + "=" * 60)
        print("✅ VALIDATION ET TEST TERMINÉS")
        print("=" * 60)
        print(f"\n📌 Prochaine étape : python scripts/inference.py")
        print(f"   Pour tester le modèle en temps réel sur des images/vidéos")

    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        raise


if __name__ == "__main__":
    main()
