# WebWise AI 🤖

Un assistant intelligent pour le développement web, combinant génération de code, analyse d'accessibilité et traitement d'images. Ce projet utilise StarCoder-3b pour la génération de code et l'analyse, avec une architecture moderne Django/FastAPI.

## 🌟 Fonctionnalités

- Génération de code HTML/CSS accessible et sémantique
- Analyse et suggestions d'amélioration de code
- Conversion de maquettes en code (à venir)
- Explications détaillées des choix techniques
- Interface utilisateur intuitive

## 🔧 Technologies

- StarCoder-3b pour l'analyse et la génération de code
- Django pour l'application principale
- FastAPI pour les services d'IA
- React pour l'interface utilisateur
- PostgreSQL pour la base de données

## 🚀 Installation

1. Prérequis :

   - Python 3.9+
   - Node.js 16+
   - PostgreSQL 13+

2. Installation :

```bash
# Cloner le repository
git clone https://github.com/votre-nom/webwise-ai.git
cd webwise-ai

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # ou .\venv\Scripts\activate sur Windows

# Installer les dépendances
pip install -r requirements.txt
```

3. Configuration :

   - Copier `.env.example` en `.env`
   - Configurer les variables d'environnement

4. Lancer l'application :

```bash
python manage.py runserver
```

## 📖 Documentation

La documentation complète est disponible dans le dossier `docs/` :

- Guide du projet : `docs/project_guide.md`
- Feuille de route : `docs/roadmap.md`
- Documentation API : `docs/api/`

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez `CONTRIBUTING.md` pour les directives.

## 📝 License

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## 🙏 Remerciements

- Équipe HuggingFace pour StarCoder-3b
- Communauté Django
- Contributeurs du projet
