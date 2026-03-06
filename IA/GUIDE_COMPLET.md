# 📚 Guide Complet - Détection du Code Vestimentaire ENSITECH

## 🎯 Vue d'ensemble du projet

Ce projet utilise l'intelligence artificielle (YOLOv8) pour détecter automatiquement les infractions au code vestimentaire de l'école ENSITECH conformément à l'article 17 du règlement intérieur.

---

## 📋 Table des matières

1. [Architecture du projet](#architecture-du-projet)
2. [Installation](#installation)
3. [Comprendre le dataset](#comprendre-le-dataset)
4. [Pipeline d'entraînement](#pipeline-dentraînement)
5. [Évaluation et métriques](#évaluation-et-métriques)
6. [Utilisation du modèle](#utilisation-du-modèle)
7. [Optimisation et amélioration](#optimisation-et-amélioration)
8. [Intégration avec le backend](#intégration-avec-le-backend)
9. [Troubleshooting](#troubleshooting)

---

## 1. Architecture du projet

### Structure des dossiers

```
IA/
├── data/                          # Données
│   ├── raw/                       # Dataset brut (HuggingFace)
│   │   ├── train/                 # 42,100 images (90%)
│   │   ├── validation/            # 2,340 images (5%)
│   │   └── test/                  # 2,340 images (5%)
│   ├── processed/                 # Dataset au format YOLO
│   │   ├── train/
│   │   │   ├── images/
│   │   │   └── labels/            # Annotations .txt
│   │   ├── val/
│   │   └── test/
│   └── annotations/               # Métadonnées
│
├── models/                        # Modèles
│   ├── dress_code_detection_*/    # Dossiers d'entraînement
│   │   ├── weights/
│   │   │   ├── best.pt            # Meilleur modèle
│   │   │   └── last.pt            # Dernier checkpoint
│   │   ├── results.png            # Courbes d'entraînement
│   │   └── confusion_matrix.png   # Matrice de confusion
│   └── final/
│       └── best_model.pt          # Modèle de production
│
├── scripts/                       # Scripts Python
│   ├── download_data.py           # Téléchargement du dataset
│   ├── prepare_dataset.py         # Préparation pour YOLO
│   ├── train.py                   # Entraînement
│   ├── validate.py                # Validation
│   └── inference.py               # Inférence temps réel
│
├── notebooks/                     # Jupyter notebooks
│   ├── 01_data_exploration.ipynb  # Exploration du dataset
│   ├── 02_model_training.ipynb    # Entraînement interactif
│   └── 03_evaluation.ipynb        # Évaluation détaillée
│
├── results/                       # Résultats
│   ├── images/                    # Images annotées
│   ├── videos/                    # Vidéos traitées
│   ├── metrics/                   # Métriques JSON
│   └── reports/                   # Rapports
│
├── logs/                          # Logs TensorBoard
│
├── config.yaml                    # Configuration du projet
├── requirements.txt               # Dépendances Python
├── README.md                      # Documentation principale
├── QUICKSTART.md                  # Guide de démarrage rapide
└── GUIDE_COMPLET.md              # Ce fichier
```

---

## 2. Installation

### 2.1 Prérequis

- **Python** : 3.9+ (Python 3.13 recommandé)
- **Espace disque** : ~10 GB minimum
- **RAM** : 8 GB minimum (16 GB recommandé)
- **GPU** : Optionnel mais fortement recommandé
  - NVIDIA GPU avec CUDA (Linux/Windows)
  - Apple Silicon M1/M2/M3 avec MPS (macOS)

### 2.2 Installation pas à pas

```bash
# 1. Aller dans le dossier IA
cd IA

# 2. Activer l'environnement virtuel
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# 3. Vérifier l'installation
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "from ultralytics import YOLO; print('YOLOv8: OK')"
```

**Résultat attendu :**
```
✅ PyTorch 2.9.1
✅ CUDA disponible: False
✅ MPS disponible: True
✅ YOLOv8 installé avec succès
```

---

## 3. Comprendre le dataset

### 3.1 Dataset Fashionpedia

- **Source** : [HuggingFace - Fashionpedia 4 Categories](https://huggingface.co/datasets/detection-datasets/fashionpedia_4_categories)
- **Taille** : 46,780 images (~3.5 GB)
- **Format** : Images JPEG avec annotations de bounding boxes

**Catégories d'origine :**

| ID | Catégorie   | Description                    |
|----|-------------|--------------------------------|
| 0  | Accessories | Lunettes, chapeaux, ceintures  |
| 1  | Bags        | Sacs, portefeuilles            |
| 2  | Clothing    | Vêtements (hauts, bas)         |
| 3  | Shoes       | Chaussures                     |

### 3.2 Mapping vers le code vestimentaire ENSITECH

**Notre mapping :**

| ID YOLO | Catégorie             | Fashionpedia | Description                                      |
|---------|-----------------------|--------------|--------------------------------------------------|
| 0       | accessoire_interdit   | 0            | Casquette, chapeau, bonnet, bandana              |
| 1       | vetement_interdit     | 2            | Crop top, dos ouvert, short, bermuda, mini-jupe  |
| 2       | chaussure_interdite   | 3            | Tongs                                            |

**Catégorie ignorée :** Bags (ID 1) - non concerné par le règlement

### 3.3 Limitations du dataset

⚠️ **Important** : Le dataset Fashionpedia est généraliste. Il ne distingue pas :
- Crop tops vs T-shirts normaux
- Shorts vs pantalons
- Tongs vs autres chaussures

**Solution :** En première approche, le modèle détecte toutes les instances des catégories. Vous pourrez :
1. **Affiner plus tard** avec vos propres images annotées
2. **Filtrer** par règles post-détection (ex: hauteur du vêtement)
3. **Utiliser** un modèle de classification supplémentaire

---

## 4. Pipeline d'entraînement

### 4.1 Étape 1 : Télécharger le dataset

```bash
python scripts/download_data.py
```

**Ce script :**
- Télécharge 46,780 images depuis HuggingFace
- Les organise en train/validation/test
- Génère `data/raw/metadata.json`

**Durée estimée :** 30 min - 1h (selon connexion)

### 4.2 Étape 2 : Préparer pour YOLO

```bash
python scripts/prepare_dataset.py
```

**Ce script :**
- Convertit les annotations au format YOLO
  - Format : `class_id x_center y_center width height`
  - Coordonnées normalisées entre 0 et 1
- Mappe les catégories Fashionpedia vers notre code vestimentaire
- Crée le fichier `data/processed/data.yaml`

**Durée estimée :** 15-30 min

**Fichier `data.yaml` généré :**
```yaml
path: /chemin/vers/data/processed
train: train/images
val: val/images
test: test/images
nc: 3
names:
  - accessoire_interdit
  - vetement_interdit
  - chaussure_interdite
```

### 4.3 Étape 3 : Entraîner le modèle

```bash
python scripts/train.py
```

**Hyperparamètres par défaut :**
```python
'model_size': 'yolov8n',    # Nano (rapide)
'epochs': 100,              # Nombre d'époques
'batch_size': 16,           # Taille du batch
'imgsz': 640,               # Taille d'image
'optimizer': 'Adam',        # Optimiseur
'lr0': 0.01,               # Learning rate initial
```

**Durée estimée :**
- GPU NVIDIA : 2-4h
- Apple M1/M2 (MPS) : 4-6h
- CPU : 8-12h

**Métriques suivies :**
- **Loss** : Fonction de perte (à minimiser)
- **mAP@0.5** : Précision moyenne à 50% IoU
- **mAP@0.5:0.95** : Précision moyenne sur plusieurs seuils
- **Precision** : % de détections correctes
- **Recall** : % d'objets détectés

**Courbes d'entraînement :**
Le script génère automatiquement :
- `results.png` : Courbes de loss, mAP, precision, recall
- `confusion_matrix.png` : Matrice de confusion

### 4.4 Étape 4 : Valider le modèle

```bash
python scripts/validate.py
```

**Ce script :**
- Évalue sur l'ensemble de validation
- Évalue sur l'ensemble de test
- Génère des rapports JSON

**Métriques clés :**
```
📊 RÉSULTATS DE LA VALIDATION
═════════════════════════════
🎯 Métriques globales :
   mAP@0.5      : 0.8542
   mAP@0.5:0.95 : 0.6231
   Precision    : 0.8921
   Recall       : 0.7854
   F1-Score     : 0.8351

📈 Métriques par classe :
   accessoire_interdit    : 0.9012
   vetement_interdit      : 0.8542
   chaussure_interdite    : 0.8072
```

---

## 5. Évaluation et métriques

### 5.1 Comprendre les métriques

#### IoU (Intersection over Union)
```
IoU = Aire de l'intersection / Aire de l'union

Exemple :
  ┌─────────┐
  │ Pred.   │
  │    ┌────┼─────┐
  │    │ ∩  │     │
  └────┼────┘     │
       │   GT     │
       └──────────┘

IoU = Aire(∩) / (Aire(Pred) + Aire(GT) - Aire(∩))
```

#### mAP (Mean Average Precision)
- **mAP@0.5** : Précision moyenne avec IoU ≥ 0.5
- **mAP@0.5:0.95** : Moyenne des mAP de 0.5 à 0.95 par pas de 0.05

#### Precision vs Recall
```
Precision = TP / (TP + FP)  # % détections correctes
Recall    = TP / (TP + FN)  # % objets détectés

TP = Vrais Positifs
FP = Faux Positifs
FN = Faux Négatifs
```

#### F1-Score
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

### 5.2 Objectifs du projet

| Métrique            | Objectif | Justification                              |
|---------------------|----------|--------------------------------------------|
| Precision           | ≥ 90%    | Minimiser les fausses alertes              |
| Recall              | ≥ 80%    | Détecter la majorité des infractions       |
| Temps d'inférence   | < 2s     | Contrainte temps réel                      |
| Faux positifs       | < 5%     | Éviter trop d'alertes inutiles             |

### 5.3 Interpréter les résultats

**Exemple de rapport :**
```json
{
  "mAP50": 0.8542,
  "mAP50-95": 0.6231,
  "precision": 0.8921,
  "recall": 0.7854,
  "f1_score": 0.8351
}
```

**Interprétation :**
- ✅ **Precision 89%** : Sur 100 détections, 89 sont correctes
- ⚠️ **Recall 78%** : Le modèle détecte 78% des infractions
- ℹ️ **F1-Score 83%** : Bon équilibre precision/recall

**Actions possibles :**
- Si **Precision faible** → Augmenter le seuil de confiance
- Si **Recall faible** → Augmenter les époques, utiliser plus de données

---

## 6. Utilisation du modèle

### 6.1 Inférence sur une image

```bash
python scripts/inference.py --source image.jpg
```

**Sortie :**
```
🖼️  Analyse de l'image : image.jpg

⚠️  2 infraction(s) détectée(s) :
   - vetement_interdit (confiance: 87.23%)
   - accessoire_interdit (confiance: 92.15%)

⏱️  Temps d'inférence : 0.342s
✅ Objectif atteint (< 2s)
```

### 6.2 Inférence sur une vidéo

```bash
python scripts/inference.py --source video.mp4
```

### 6.3 Inférence en temps réel (webcam)

```bash
python scripts/inference.py --source 0
```

**Contrôles :**
- **Q** : Quitter
- **Espace** : Pause (à implémenter si besoin)

### 6.4 Options avancées

```bash
# Ajuster le seuil de confiance
python scripts/inference.py --source 0 --conf 0.7

# Ne pas sauvegarder les résultats
python scripts/inference.py --source 0 --no-save

# Taille d'image personnalisée
python scripts/inference.py --source 0 --imgsz 416
```

---

## 7. Optimisation et amélioration

### 7.1 Si la précision est insuffisante (< 90%)

#### Option 1 : Augmenter les époques

```python
# Dans scripts/train.py, ligne 30
'epochs': 200  # au lieu de 100
```

#### Option 2 : Utiliser un modèle plus grand

```python
# Dans scripts/train.py, ligne 25
'model_size': 'yolov8s'  # au lieu de 'yolov8n'
```

**Comparaison des modèles :**

| Modèle  | Taille | Vitesse | Précision | Utilisation                |
|---------|--------|---------|-----------|----------------------------|
| YOLOv8n | 3 MB   | ★★★★★   | ★★★☆☆     | Tests rapides, démos       |
| YOLOv8s | 11 MB  | ★★★★☆   | ★★★★☆     | Bon compromis              |
| YOLOv8m | 26 MB  | ★★★☆☆   | ★★★★★     | Production, précision      |
| YOLOv8l | 44 MB  | ★★☆☆☆   | ★★★★★     | Haute précision            |
| YOLOv8x | 68 MB  | ★☆☆☆☆   | ★★★★★     | Maximum de précision       |

#### Option 3 : Augmenter la résolution

```python
# Dans scripts/train.py, ligne 33
'imgsz': 1280  # au lieu de 640
```

⚠️ **Attention** : Augmente le temps d'entraînement et la VRAM nécessaire

#### Option 4 : Ajuster les augmentations

```python
# Dans scripts/train.py, lignes 42-52
'hsv_s': 0.9,      # Plus de variation de couleur
'flipud': 0.5,     # Retournement vertical
'mosaic': 1.0,     # Augmentation mosaïque
'mixup': 0.2,      # Mélange d'images
```

#### Option 5 : Affiner avec vos propres données

1. Collecter des images d'étudiants (avec consentement)
2. Annoter avec [LabelImg](https://github.com/tzutalin/labelImg) ou [CVAT](https://cvat.ai/)
3. Ajouter au dataset
4. Ré-entraîner

### 7.2 Si l'inférence est trop lente (> 2s)

#### Option 1 : Utiliser YOLOv8n

Le modèle le plus rapide.

#### Option 2 : Réduire la résolution

```bash
python scripts/inference.py --source 0 --imgsz 416
```

#### Option 3 : Exporter vers ONNX

```python
from ultralytics import YOLO

model = YOLO('models/final/best_model.pt')
model.export(format='onnx')
```

**Avantages ONNX :**
- Plus rapide (optimisations)
- Compatible multi-plateformes
- Peut être optimisé avec TensorRT (NVIDIA)

#### Option 4 : Quantification

```python
model.export(format='onnx', int8=True)  # Quantification INT8
```

**Gain :** ~2-4x plus rapide, légère perte de précision

### 7.3 Réduire les faux positifs

#### Option 1 : Augmenter le seuil de confiance

```bash
python scripts/inference.py --source 0 --conf 0.7  # au lieu de 0.5
```

#### Option 2 : Post-traitement

Ajouter des règles métier :
```python
def is_valid_detection(bbox, class_id, confidence):
    # Filtrer les détections trop petites
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    area = width * height
    
    if area < 0.05:  # < 5% de l'image
        return False
    
    # Filtrer par position
    if class_id == 2 and bbox[3] < 0.7:  # Chaussures en haut de l'image
        return False
    
    return True
```

---

## 8. Intégration avec le backend

### 8.1 API REST avec FastAPI

**Créer un fichier `api.py` :**

```python
from fastapi import FastAPI, File, UploadFile
from ultralytics import YOLO
import numpy as np
from PIL import Image
import io

app = FastAPI()
model = YOLO('models/final/best_model.pt')

@app.post("/detect")
async def detect_violations(file: UploadFile = File(...)):
    """
    Détecte les infractions au code vestimentaire
    """
    # Lire l'image
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    
    # Prédiction
    results = model.predict(source=image, conf=0.5)
    
    # Extraire les détections
    detections = []
    for box in results[0].boxes:
        detections.append({
            'class': model.names[int(box.cls[0])],
            'confidence': float(box.conf[0]),
            'bbox': box.xyxy[0].tolist()
        })
    
    return {
        'violations_detected': len(detections) > 0,
        'num_violations': len(detections),
        'detections': detections
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

**Lancer l'API :**
```bash
pip install fastapi uvicorn
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Tester :**
```bash
curl -X POST "http://localhost:8000/detect" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg"
```

### 8.2 Intégration avec le backend Node.js

**Exemple d'appel depuis Node.js :**

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function detectViolations(imagePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(imagePath));
    
    const response = await axios.post(
        'http://localhost:8000/detect',
        form,
        { headers: form.getHeaders() }
    );
    
    return response.data;
}

// Utilisation
detectViolations('image.jpg').then(result => {
    if (result.violations_detected) {
        console.log(`⚠️ ${result.num_violations} violation(s) détectée(s)`);
        
        // Envoyer une alerte
        sendAlert(result.detections);
    }
});
```

### 8.3 Système d'alertes

**Exemple d'envoi d'email :**

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

def send_alert(detections, image_path):
    msg = MIMEMultipart()
    msg['Subject'] = f'⚠️ Alerte Code Vestimentaire - {len(detections)} infraction(s)'
    msg['From'] = 'alert@ensitech.fr'
    msg['To'] = 'responsable@ensitech.fr'
    
    # Corps du message
    body = f"""
    Détection d'infraction au code vestimentaire
    
    Date/Heure : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    Nombre d'infractions : {len(detections)}
    
    Détails :
    """
    
    for i, det in enumerate(detections, 1):
        body += f"\n{i}. {det['class']} (confiance: {det['confidence']:.2%})"
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Joindre l'image
    with open(image_path, 'rb') as f:
        img = MIMEImage(f.read())
        msg.attach(img)
    
    # Envoyer
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('alert@ensitech.fr', 'password')
        server.send_message(msg)
```

---

## 9. Troubleshooting

### 9.1 Erreurs fréquentes

#### Erreur : "CUDA out of memory"

**Solution 1 :** Réduire le batch size
```python
# Dans train.py
'batch_size': 8  # au lieu de 16
```

**Solution 2 :** Réduire la taille d'image
```python
'imgsz': 416  # au lieu de 640
```

#### Erreur : "No module named 'ultralytics'"

**Solution :**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Erreur : Dataset non trouvé

**Vérifier :**
```bash
ls -la data/raw/
ls -la data/processed/
```

**Solution :**
```bash
python scripts/download_data.py
python scripts/prepare_dataset.py
```

#### Erreur : Webcam ne fonctionne pas

**Tester :**
```python
import cv2
cap = cv2.VideoCapture(0)
print('✅ OK' if cap.isOpened() else '❌ Erreur')
```

**Sur macOS :** Vérifier les permissions dans Préférences Système → Confidentialité → Caméra

### 9.2 Performances insuffisantes

#### Problème : mAP < 70%

**Causes possibles :**
- Pas assez d'époques
- Modèle trop petit
- Learning rate inadapté
- Déséquilibre des classes

**Solutions :**
1. Augmenter les époques à 200-300
2. Utiliser YOLOv8s ou YOLOv8m
3. Ajuster le learning rate
4. Utiliser class weights pour équilibrer

#### Problème : Overfitting

**Symptômes :**
- Train loss diminue mais val loss augmente
- mAP train >> mAP val

**Solutions :**
1. Augmenter l'augmentation de données
2. Ajouter du dropout (si possible)
3. Réduire la taille du modèle
4. Utiliser early stopping (déjà implémenté)

### 9.3 Support et ressources

**Documentation officielle :**
- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [PyTorch Docs](https://pytorch.org/docs/)

**Communauté :**
- [YOLOv8 GitHub Issues](https://github.com/ultralytics/ultralytics/issues)
- [PyTorch Forums](https://discuss.pytorch.org/)

**Contact projet :**
- Équipe IA ENSITECH

---

## 📌 Checklist complète

### Phase 1 : Setup (✅ Terminé)
- [x] Environnement virtuel activé
- [x] Dépendances installées
- [x] GPU/MPS détecté

### Phase 2 : Données
- [ ] Dataset téléchargé (3.5 GB)
- [ ] Dataset préparé au format YOLO
- [ ] Notebook d'exploration exécuté

### Phase 3 : Entraînement
- [ ] Modèle entraîné (100+ époques)
- [ ] Validation effectuée
- [ ] Métriques analysées

### Phase 4 : Tests
- [ ] Test sur images
- [ ] Test sur vidéo
- [ ] Test webcam temps réel

### Phase 5 : Production
- [ ] Modèle optimisé (ONNX)
- [ ] API REST créée
- [ ] Intégration backend
- [ ] Système d'alertes

---

## 🎉 Conclusion

Vous avez maintenant tous les outils pour :
1. ✅ Entraîner un modèle YOLOv8
2. ✅ Détecter les infractions au code vestimentaire
3. ✅ Évaluer et optimiser les performances
4. ✅ Déployer en production

**Prochaines étapes recommandées :**
1. Lancer `python scripts/download_data.py`
2. Explorer le dataset avec le notebook
3. Entraîner le modèle
4. Tester en temps réel
5. Affiner avec vos propres données

Bon courage ! 🚀
