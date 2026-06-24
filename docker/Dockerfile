# Image de base légère
FROM python:3.11-alpine

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances en premier (optimisation du cache Docker)
COPY app/requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY app/ .

# Exposer le port
EXPOSE 80

# Lancer l'application
CMD ["python", "app.py"]
