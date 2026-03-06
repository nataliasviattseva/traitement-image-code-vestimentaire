"""
Script d'inférence en temps réel pour la détection du code vestimentaire
Supporte : images, vidéos, webcam
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

# Configuration
BASE_DIR = Path(__file__).parent.parent
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


def predict_image(model, image_path, conf_threshold=0.5, save=True):
    """
    Prédiction sur une seule image

    Args:
        model: Modèle YOLO
        image_path: Chemin vers l'image
        conf_threshold: Seuil de confiance
        save: Sauvegarder l'image avec les détections
    """
    print(f"\n🖼️  Analyse de l'image : {image_path}")

    start_time = time.time()

    # Prédiction
    results = model.predict(
        source=str(image_path),
        conf=conf_threshold,
        save=save,
        project=str(RESULTS_DIR / "images"),
        name="predictions",
        exist_ok=True,
    )

    inference_time = time.time() - start_time

    # Analyser les résultats
    result = results[0]
    detections = []

    if len(result.boxes) > 0:
        print(f"\n⚠️  {len(result.boxes)} infraction(s) détectée(s) :")

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = model.names[class_id]

            detection = {
                "class": class_name,
                "confidence": confidence,
                "bbox": box.xyxy[0].tolist(),
            }
            detections.append(detection)

            print(f"   - {class_name} (confiance: {confidence:.2%})")
    else:
        print(f"\n✅ Aucune infraction détectée")

    print(f"\n⏱️  Temps d'inférence : {inference_time:.3f}s")

    # Vérifier l'objectif de temps
    if inference_time > 2.0:
        print(f"⚠️  Objectif non atteint (< 2s)")
    else:
        print(f"✅ Objectif atteint (< 2s)")

    return {
        "detections": detections,
        "inference_time": inference_time,
        "num_violations": len(detections),
    }


def predict_video(model, video_source, conf_threshold=0.5, save=True):
    """
    Prédiction sur une vidéo ou webcam

    Args:
        model: Modèle YOLO
        video_source: Chemin vers la vidéo ou '0' pour webcam
        conf_threshold: Seuil de confiance
        save: Sauvegarder la vidéo avec les détections
    """
    # Ouvrir la source vidéo
    if video_source == "0" or video_source == 0:
        print(f"\n📹 Ouverture de la webcam...")
        cap = cv2.VideoCapture(0)
        source_name = "webcam"
    else:
        print(f"\n📹 Ouverture de la vidéo : {video_source}")
        cap = cv2.VideoCapture(str(video_source))
        source_name = Path(video_source).stem

    if not cap.isOpened():
        raise ValueError(f"❌ Impossible d'ouvrir la source vidéo : {video_source}")

    # Paramètres de la vidéo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"   Résolution : {width}x{height}")
    print(f"   FPS : {fps}")

    # Préparer l'enregistrement
    if save:
        output_dir = RESULTS_DIR / "videos"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = (
            output_dir
            / f"{source_name}_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        print(f"   Sauvegarde dans : {output_path}")

    print(f"\n🎬 Démarrage de la détection...")
    print(f"   Appuyez sur 'q' pour quitter")

    frame_count = 0
    total_inference_time = 0
    violation_frames = 0

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            frame_count += 1
            start_time = time.time()

            # Prédiction
            results = model.predict(source=frame, conf=conf_threshold, verbose=False)

            inference_time = time.time() - start_time
            total_inference_time += inference_time

            # Annoter l'image
            annotated_frame = results[0].plot()

            # Compter les violations
            num_violations = len(results[0].boxes)
            if num_violations > 0:
                violation_frames += 1

            # Afficher les informations
            fps_text = (
                f"FPS: {1 / inference_time:.1f}" if inference_time > 0 else "FPS: N/A"
            )
            cv2.putText(
                annotated_frame,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            if num_violations > 0:
                violation_text = f"Violations: {num_violations}"
                cv2.putText(
                    annotated_frame,
                    violation_text,
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )

            # Sauvegarder la frame
            if save:
                out.write(annotated_frame)

            # Afficher
            cv2.imshow("Detection du Code Vestimentaire", annotated_frame)

            # Quitter avec 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\n\n⏹️  Arrêt demandé par l'utilisateur")

    finally:
        # Nettoyer
        cap.release()
        if save:
            out.release()
        cv2.destroyAllWindows()

        # Statistiques
        avg_inference_time = (
            total_inference_time / frame_count if frame_count > 0 else 0
        )
        avg_fps = frame_count / total_inference_time if total_inference_time > 0 else 0

        print(f"\n📊 Statistiques :")
        print(f"   Frames traitées : {frame_count}")
        print(
            f"   Frames avec violations : {violation_frames} ({violation_frames / frame_count * 100:.1f}%)"
            if frame_count > 0
            else "   Frames avec violations : 0"
        )
        print(f"   Temps d'inférence moyen : {avg_inference_time:.3f}s")
        print(f"   FPS moyen : {avg_fps:.1f}")

        if avg_inference_time > 0.5:  # Pour 2fps minimum
            print(f"⚠️  Performance à améliorer pour le temps réel")
        else:
            print(f"✅ Performance temps réel atteinte")

        if save:
            print(f"\n💾 Vidéo sauvegardée : {output_path}")


def main():
    """
    Fonction principale avec arguments en ligne de commande
    """
    parser = argparse.ArgumentParser(
        description="Détection du code vestimentaire en temps réel"
    )

    parser.add_argument(
        "--source",
        type=str,
        default="0",
        help="Source : 0 pour webcam, chemin vers image/vidéo",
    )

    parser.add_argument(
        "--conf", type=float, default=0.5, help="Seuil de confiance (0.0-1.0)"
    )

    parser.add_argument(
        "--no-save", action="store_true", help="Ne pas sauvegarder les résultats"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DÉTECTION DU CODE VESTIMENTAIRE")
    print("ENSITECH - Inférence Temps Réel")
    print("=" * 60)

    try:
        # Charger le modèle
        model = load_model()

        save = not args.no_save

        # Déterminer le type de source
        if args.source == "0" or args.source == "0":
            # Webcam
            predict_video(model, 0, args.conf, save)
        else:
            source_path = Path(args.source)

            if not source_path.exists():
                print(f"❌ Fichier non trouvé : {args.source}")
                return

            # Vérifier si c'est une image ou une vidéo
            image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]
            video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv"]

            if source_path.suffix.lower() in image_extensions:
                # Image
                result = predict_image(model, source_path, args.conf, save)

                # Sauvegarder le rapport
                if save:
                    report_path = (
                        RESULTS_DIR
                        / "reports"
                        / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    report_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(report_path, "w") as f:
                        json.dump(result, f, indent=4)

                    print(f"\n💾 Rapport sauvegardé : {report_path}")

            elif source_path.suffix.lower() in video_extensions:
                # Vidéo
                predict_video(model, source_path, args.conf, save)

            else:
                print(f"❌ Format non supporté : {source_path.suffix}")
                print(f"   Images : {', '.join(image_extensions)}")
                print(f"   Vidéos : {', '.join(video_extensions)}")

        print("\n" + "=" * 60)
        print("✅ DÉTECTION TERMINÉE")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        raise


if __name__ == "__main__":
    main()
