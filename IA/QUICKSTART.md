# 🚀 Guide de Démarrage Rapide

## ⚡ Installation en 5 minutes

### 1. Activer l'environnement virtuel

```bash
cd IA
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows
```

### 2. Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note :** L'installation peut prendre 5-10 minutes selon votre connexion.

### 3. Vérifier l'installation

```bash
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')"
python -c "from ultralytics import YOLO; print('✅ YOLOv8 installé')"
```

## 📊 Pipeline d'entraînement complet

### Étape 1 : Télécharger le dataset (30 min - 1h)

```bash
python scripts/download_data.py
```

Ce script :
- Télécharge ~46,000 images depuis HuggingFace
- Crée la structure de dossiers
- Génère les métadonnées

**Taille :** ~3.5 GB

### Étape 2 : Préparer le dataset (15-30 min)

```bash
python scripts/prepare_dataset.py
```

Ce script :
- Convertit les annotations au format YOLO
- Mappe les catégories vers le code vestimentaire ENSITECH
- Split : train (90%) / val (5%) / test (5%)
- Génère le fichier `data.yaml`

### Étape 3 : Entraîner le modèle (2-8h selon GPU)

```bash
python scripts/train.py
```

**Paramètres par défaut :**
- Modèle : YOLOv8n (nano - rapide)
- Époques : 100
- Batch size : 16
- Image size : 640x640

**Temps estimé :**
- Avec GPU (NVIDIA) : 2-4h
- Avec Apple Silicon (M1/M2) : 4-6h
- Sans GPU (CPU) : 8-12h

**Astuce :** Pour un test rapide, modifiez `epochs=10` dans `train.py`

### Étape 4 : Valider le modèle (5-10 min)

```bash
python scripts/validate.py
```

Évalue le modèle sur les ensembles de validation et de test.

### Étape 5 : Tester en temps réel

#### Image unique

```bash
python scripts/inference.py --source chemin/vers/image.jpg
```

#### Vidéo

```bash
python scripts/inference.py --source chemin/vers/video.mp4
```

#### Webcam

```bash
python scripts/inference.py --source 0
```

#### Options

```bash
# Ajuster le seuil de confiance
python scripts/inference.py --source 0 --conf 0.7

# Ne pas sauvegarder les résultats
python scripts/inference.py --source 0 --no-save
```

## 🎯 Catégories détectées

### Mapping Fashionpedia → Code Vestimentaire ENSITECH

| ID | Catégorie YOLO | Description | Fashionpedia |
|----|----------------|-------------|--------------|
| 0  | accessoire_interdit | Casquette, chapeau, bonnet, bandana | Accessories |
| 1  | vetement_interdit | Crop top, dos ouvert, tenue sport, short, bermuda, mini-jupe, baggy, jean troué | Clothing |
| 2  | chaussure_interdite | Tongs | Shoes |

**Note :** Les "Bags" ne sont pas concernés par le règlement et sont ignorés.

## 📈 Métriques attendues

### Objectifs du projet

| Métrique | Objectif | Comment l'atteindre |
|----------|----------|---------------------|
| Précision | ≥ 90% | Augmenter les époques, utiliser YOLOv8s/m |
| Temps d'inférence | < 2s | Utiliser YOLOv8n, optimiser avec ONNX |
| Taux de faux positifs | < 5% | Ajuster le seuil de confiance |

### Interprétation des métriques

- **mAP@0.5** : Précision moyenne à 50% IoU (seuil principal)
- **mAP@0.5:0.95** : Précision moyenne sur plusieurs seuils
- **Precision** : % de détections correctes parmi toutes les détections
- **Recall** : % d'objets détectés parmi tous les objets présents

## 🛠️ Amélioration du modèle

### Si la précision est insuffisante (< 90%)

1. **Augmenter les époques**
   ```python
   # Dans train.py, ligne ~30
   'epochs': 200  # au lieu de 100
   ```

2. **Utiliser un modèle plus grand**
   ```python
   # Dans train.py, ligne ~25
   'model_size': 'yolov8s'  # au lieu de 'yolov8n'
   # Options : yolov8n < yolov8s < yolov8m < yolov8l < yolov8x
   ```

3. **Augmenter la taille d'image**
   ```python
   # Dans train.py, ligne ~33
   'imgsz': 1280  # au lieu de 640
   ```

4. **Ajuster les augmentations**
   ```python
   # Dans train.py, lignes 42-52
   'hsv_s': 0.9,      # Plus d'augmentation de couleur
   'flipud': 0.5,     # Retournement vertical
   'mosaic': 1.0,     # Augmentation mosaïque
   'mixup': 0.2,      # Mélange d'images
   ```

### Si l'inférence est trop lente (> 2s)

1. **Utiliser YOLOv8n** (le plus rapide)

2. **Réduire la taille d'image**
   ```bash
   # Lors de l'inférence
   python scripts/inference.py --source 0 --imgsz 416
   ```

3. **Exporter vers ONNX** (plus rapide)
   ```python
   from ultralytics import YOLO
   model = YOLO('models/final/best_model.pt')
   model.export(format='onnx')
   ```

4. **Utiliser un GPU** si possible

## 📁 Structure des résultats

```
IA/
├── models/
│   ├── dress_code_detection_YYYYMMDD_HHMMSS/  # Dossier d'entraînement
│   │   ├── weights/
│   │   │   ├── best.pt         # Meilleur modèle
│   │   │   └── last.pt         # Dernier checkpoint
│   │   ├── results.png         # Courbes d'entraînement
│   │   └── confusion_matrix.png
│   └── final/
│       └── best_model.pt       # Modèle final (copie)
│
├── results/
│   ├── images/                 # Images avec détections
│   ├── videos/                 # Vidéos traitées
│   ├── metrics/                # JSON des métriques
│   └── reports/                # Rapports d'inférence
│
└── logs/                       # Logs d'entraînement
```

## ⚠️ Problèmes courants

### Erreur : "CUDA out of memory"

**Solution :** Réduire le batch size
```python
# Dans train.py
'batch_size': 8  # au lieu de 16
```

### Erreur : "No module named 'ultralytics'"

**Solution :** Réinstaller les dépendances
```bash
pip install -r requirements.txt
```

### Dataset non trouvé

**Solution :** Vérifier que vous avez bien exécuté les étapes 1 et 2
```bash
ls -la data/raw/
ls -la data/processed/
```

### Webcam ne fonctionne pas

**Solution :** Vérifier les permissions caméra
```bash
# Tester avec OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print('✅ OK' if cap.isOpened() else '❌ Erreur')"
```

## 🎓 Ressources supplémentaires

### Documentation

- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [PyTorch Docs](https://pytorch.org/docs/)
- [Dataset Fashionpedia](https://huggingface.co/datasets/detection-datasets/fashionpedia_4_categories)

### Tutoriels

- [YOLOv8 Training](https://docs.ultralytics.com/modes/train/)
- [Custom Dataset](https://docs.ultralytics.com/datasets/)
- [Model Export](https://docs.ultralytics.com/modes/export/)

## 📞 Support

Pour toute question ou problème :
1. Vérifier ce guide
2. Consulter les logs : `logs/`
3. Vérifier les issues GitHub d'Ultralytics
4. Contacter l'équipe IA du projet

## ✅ Checklist de démarrage

- [ ] Environnement virtuel activé
- [ ] Dépendances installées
- [ ] Dataset téléchargé (~3.5 GB)
- [ ] Dataset préparé au format YOLO
- [ ] Modèle entraîné (ou en cours)
- [ ] Validation effectuée
- [ ] Test temps réel sur webcam/vidéo

**Temps total estimé :** 4-10 heures (selon matériel)

## 🚀 Prêt à commencer ?

```bash
cd IA
source venv/bin/activate
python scripts/download_data.py
```

Bon entraînement ! 🎉
