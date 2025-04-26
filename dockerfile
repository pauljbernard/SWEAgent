# Utiliser une image Python légère
FROM python:3.12-slim

# Installer supervisord et autres dépendances
RUN apt-get update && apt-get install -y \
    #supervisor \
    curl git \
    && apt-get clean

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires dans le conteneur
COPY . /app
RUN chmod +x /app/serve_classifier.sh /app/serve_libraire.sh

# Copier le fichier de configuration supervisord
#COPY ./supervisord.conf /etc/supervisor/supervisord.conf

# Mettre à jour pip et installer les dépendances Python
RUN /usr/local/bin/python3 -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

RUN pip show gradio

# Exposer le port 7860
EXPOSE 7860

# Commande pour lancer supervisord
#CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
CMD ["python", "chat.py"]
