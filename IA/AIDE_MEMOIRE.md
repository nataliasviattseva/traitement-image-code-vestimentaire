# 📝 Aide-Mémoire - Commandes Essentielles

## 🔥 Commandes les plus utilisées

### Activation de l'environnement
```bash
cd ~/Documents/M1/bigData/traitement-image-code-vestimentaire/IA
source venv/bin/activate
```

### Pipeline complet
```bash
# 1. Télécharger le dataset (30-60 min)
python scripts/download_data.py

# 2. Préparer pour YOLO (15-30 min)
python scripts/prepare_dataset.py

# 3. Entraîner (2-8h selon GPU)
python scripts/train.py

# 4. Valider
python scripts/validate.py

# 5. Tester en temps réel
python scripts/inference.py --source 0
```

---

## 📊 Commandes d'inférence

### Image unique
```bash
python scripts/inference.py --source image.jpg
```

### Vidéo
```bash
python scripts/inference.py --source video.mp4
```

### Webcam
```bash
python scripts/inference.py --source 0
```

### Options
```bash
# Seuil de confiance plus élevé
python scripts/inference.py --source 0 --conf 0.7

# Ne pas sauvegarder
python scripts/inference.py --source 0 --no-save
```

---

## 🔧 Vérifications rapides

### Vérifier l'installation
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "from ultralytics import YOLO; print('YOLO OK')"
python -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"
```

### Vérifier le dataset
```bash
ls -lh data/raw/
ls -lh data/processed/
cat data/processed/data.yaml
```

### Vérifier les modèles
```bash
ls -lh models/
ls -lh models/final/
```

---

## 📓 Jupyter Notebook

### Lancer Jupyter
```bash
source venv/bin/activate
jupyter notebook
```

### Ouvrir l'exploration
```bash
jupyter notebook notebooks/01_data_exploration.ipynb
```

---

## 🎛️ Modifier les hyperparamètres

### Dans `scripts/train.py`

```python
# Ligne 25 - Taille du modèle
'model_size': 'yolov8n'  # n, s, m, l, x

# Ligne 30 - Nombre d'époques
'epochs': 100

# Ligne 31 - Taille du batch
'batch_size': 16

# Ligne 32 - Taille d'image
'imgsz': 640

# Ligne 35 - Learning rate
'lr0': 0.01
```

---

## 🐛 Dépannage rapide

### Erreur "CUDA out of memory"
```python
# Dans train.py, ligne 31
'batch_size': 8  # au lieu de 16
```

### Entraînement trop long
```python
# Dans train.py, ligne 30
'epochs': 20  # pour tester rapidement
```

### Dataset non trouvé
```bash
# Ré-exécuter
python scripts/download_data.py
python scripts/prepare_dataset.py
```

### Webcam ne marche pas
```python
# Tester avec OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Erreur')"
```

---

## 📈 Analyser les résultats

### Fichiers générés après entraînement
```bash
# Dossier de l'entraînement
ls models/dress_code_detection_*/

# Modèles
ls models/dress_code_detection_*/weights/
# - best.pt : meilleur modèle
# - last.pt : dernier checkpoint

# Graphiques
open models/dress_code_detection_*/results.png
open models/dress_code_detection_*/confusion_matrix.png

# Métriques
cat results/metrics/validation_*.json
```

### TensorBoard (optionnel)
```bash
tensorboard --logdir logs/
# Ouvrir http://localhost:6006
```

---

## 🚀 Optimisations

### Pour améliorer la précision
```python
# 1. Plus d'époques
'epochs': 200

# 2. Modèle plus grand
'model_size': 'yolov8s'

# 3. Plus grande résolution
'imgsz': 1280
```

### Pour améliorer la vitesse
```python
# 1. Modèle plus petit
'model_size': 'yolov8n'

# 2. Plus petite résolution
'imgsz': 416

# 3. Exporter en ONNX
from ultralytics import YOLO
model = YOLO('models/final/best_model.pt')
model.export(format='onnx')
```

---

## 📂 Structure importante

```
IA/
├── data/
│   ├── raw/              # Dataset brut HuggingFace
│   └── processed/        # Dataset YOLO
│       ├── train/
│       ├── val/
│       └── test/
│
├── models/
│   ├── dress_code_detection_*/  # Entraînements
│   └── final/
│       └── best_model.pt        # Modèle de production
│
├── scripts/
│   ├── download_data.py
│   ├── prepare_dataset.py
│   ├── train.py
│   ├── validate.py
│   └── inference.py
│
└── results/
    ├── images/           # Images annotées
    ├── videos/           # Vidéos traitées
    └── metrics/          # JSON des métriques
```

---

## 📞 Références rapides

### Documentation
- `README.md` - Vue d'ensemble
- `QUICKSTART.md` - Guide rapide
- `GUIDE_COMPLET.md` - Documentation complète
- `STATUS.md` - État du projet

### Liens externes
- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [PyTorch Docs](https://pytorch.org/docs/)
- [Dataset HuggingFace](https://huggingface.co/datasets/detection-datasets/fashionpedia_4_categories)

---

## 🎯 Métriques cibles

| Métrique | Objectif |
|----------|----------|
| Precision | ≥ 90% |
| Recall | ≥ 80% |
| mAP@0.5 | ≥ 85% |
| Temps | < 2s |

---

## 💡 Astuces

### Tester rapidement
```bash
# Entraîner avec 10 époques pour tester
# Modifier train.py ligne 30: 'epochs': 10
python scripts/train.py
```

### Surveiller l'entraînement
```bash
# Dans un autre terminal
watch -n 5 'ls -lht models/dress_code_detection_*/weights/'
```

### Nettoyer les anciens entraînements
```bash
# ATTENTION : supprime les modèles
rm -rf models/dress_code_detection_*
```

---

## ✅ Checklist avant entraînement

- [ ] Environnement activé (`source venv/bin/activate`)
- [ ] Dataset téléchargé (`data/raw/` existe)
- [ ] Dataset préparé (`data/processed/` existe)
- [ ] Espace disque disponible (>10 GB)
- [ ] GPU/MPS détecté (optionnel mais recommandé)

---

**Imprimez cette page pour l'avoir sous la main ! 📄**
