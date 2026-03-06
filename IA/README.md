# Détection de Code Vestimentaire - Module IA

## 📋 Vue d'ensemble

Module d'intelligence artificielle pour la détection automatique des infractions au code vestimentaire d'ENSITECH basé sur YOLOv8.

## 🎯 Objectif

Détecter automatiquement les vêtements non conformes au règlement intérieur.

## 🚀 Démarrage rapide

```bash
# 1. Activer l'environnement
source venv/bin/activate

# 2. Télécharger le dataset
python scripts/download_data.py

# 3. Préparer pour YOLO
python scripts/prepare_dataset.py

# 4. Entraîner
python scripts/train.py

# 5. Tester
python scripts/inference.py --source 0
```

## 📚 Documentation

- **QUICKSTART.md** - Guide de démarrage rapide
- **GUIDE_COMPLET.md** - Documentation complète
- **STATUS.md** - État du projet
- **AIDE_MEMOIRE.md** - Commandes essentielles

## 🏷️ Catégories détectées

- **accessoire_interdit** : Casquettes, chapeaux, bonnets
- **vetement_interdit** : Crop tops, shorts, tenues sport
- **chaussure_interdite** : Tongs

## 📊 Dataset

- Source : Fashionpedia 4 Categories (HuggingFace)
- 46,780 images (~3.5 GB)
- Train: 90% | Val: 5% | Test: 5%

## 🎯 Objectifs

- Précision ≥ 90%
- Temps d'inférence < 2s
- mAP@0.5 ≥ 85%
