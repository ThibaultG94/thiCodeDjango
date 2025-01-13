# ThiCodeAI 🤖

An intelligent assistant for web development, combining code generation, accessibility analysis and image processing. This project uses llama2 for code generation and analysis, with a modern Django/FastAPI architecture.

## 🌟 Features

- Accessible and semantic HTML/CSS code generation
- Code analysis and improvement suggestions
- Converting mock-ups into code (coming soon)
- Detailed explanations of technical choices
- Intuitive user interface

## 🔧 Technologies

- llama2 for code analysis and generation
- Django for the main application
- FastAPI for AI services
- React or Django Templates for the user interface
- PostgreSQL for the database

## 🚀 Installation

1. Requirements :

   - Python 3.9+
   - Node.js 16+
   - PostgreSQL 13+

2. Installation :

```bash
# Clone repository
git clone https://github.com/ThibaultG94/thicodeAi.git
cd thicodeAi

# Creating the virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Installing dependencies
pip install -r requirements.txt
```

3. Setting :

   - Copy `.env.example` en `.env`
   - Setting environment variables

4. Launch application :

```bash
python manage.py runserver
```

## 📖 Documentation

Full documentation is available in the `docs/` folder:

- Project guide : `docs/project_guide.md`
- Roadmap : `docs/roadmap.md`
- API documentation : `docs/api/`

## 📝 License

This project is licensed under the MIT license - see the LICENSE file for details.
