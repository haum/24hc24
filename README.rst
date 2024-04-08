24h du code 2024 - Odyssée d'HAUMère
====================================

Ce dépôt regroupe les fichier utilisés pour le sujet des 24h du code 2024 proposé par le HAUM

Données
-------

- docker

  Fichiers utiles pour réaliser un conteneur docker.

  Attention, la base de donnée a été changée dans la nuit lors de l'évènement et sa configuration n'est pas présente dans ce dossier (voir le fichier `settings.py` du serveur pour repassser en sqlite [simple] ou monter un serveur postgres avec les bons identifiants)

- documentation

  Les sources de la documentation

- server24hc

  Le serveur de jeu.

  Le dossier inclue une sauvegarde de la base de donnée faite le lundi matin (``db.json.xz``) qui peut être chargée dans le serveur docker à l'aide de la commande ``./manage.py loaddata db.json.xz``.

- trophy

  Fichiers de fabrication du trophée des vainqueurs [pour tous les sujets]

- utils

  Utilitaires utilisés lors du développement (dont certains inclus dans le serveur)

- web_viewer

  Sources de la visionneuse web

Utilisation en local
--------------------

Cette procédure permet d'exécuter le serveur en local, à l'adresse http://127.0.0.1:8000/

Première utilisation
''''''''''''''''''''

Cloner le dépôt :

``git clone https://github.com/haum/24hc24/`` (ou ``git clone git@github.com:haum/24hc24/``)

Et entrer dans ce dossier :

``cd 24hc24``

Créer un virtualenv :

``virtualenv venv``

Activer le virtualenv :

``source venv/bin/activate``

Installer (dans le virtualenv) les bibliothèques nécessaires pour le serveur :

``pip install -r server24hc/requirements.txt``

Procéder à l'initialisation de la base de données et charger les données sauvegardées des 24h du code :

``./server24hc/manage.py migrate``

``./server24hc/manage.py loaddata ./server24hc/db.json.xz``

Exécuter le serveur :

``./server24hc/manage.py runserver``

Autres utilisations
'''''''''''''''''''

Activer le virtualenv :

``source venv/bin/activate``

Exécuter le serveur :

``./server24hc/manage.py runserver``
