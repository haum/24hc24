WIP
===

Et si on codait
---------------

Sujet à 2 pans:
- côté joueur
- côté jeu


Côté Jeu
--------

- génère une carte
- récupère une liste de commandes
- calcule un score

Côté Joueur
-----------

- récupère une carte
- produit une liste de commandes (pour atteindre une arrivée)

Côté HAUM
---------

- serveur + base de données
- étapes:
   - attend une map
   - valide la map
   - attend un joueur
   - lui envoie la map
   - récupère les commandes
   - valide les commandes/calcule un score
   - envoie les commandes au jeu
   - attend un score
   - valide le score
   - LOG

Notation
--------

3 rounds de proposition de cartes + jeu
- round 1 (18h):
  - 2 cartes/équipes, coups max-50
- round 2 (1h):
  - 2 cartes/équipes, coups max-50
  - 5 cartes/équipes, coups max-100
- round 3 (8h):
  - 2 cartes/équipes, coups max-50
  - 5 cartes/équipes, coups max-100
  - 10 cartes/équipes, coups max-150
tous les joueurs jouent toutes les cartes à tous les rounds

- pénaliser les cartes impossibles
- pénaliser les mauvais calculs de score
- avantager les cartes peu résolues
- avantager les joueurs qui résolvent en un minimum de coups

Notation golf:

Joueur:
   - le plus rapide -> 0 points
   - autres -> +1 point/coup supplémentaire
   - échec -> +5+2*points(pire résolvant)

Jeu:
   - +1 point/joueur résolvant
   - +10 points si un score incorrect pour une map donnée (1 fois/map)
   - map impossible : +nombre de points max si tous les calculs de score incorrects

Infra
-----

- docker sur serveur HAUM
- base de données pour rejouer les matchs sur l'écran
- uniq token pour repérer joueur/jeu

Protocole
---------

All ASCII

Joueur
- liste des commandes vectorielles: liste de 3 float, longueur variable

Jeu
- map:
  liste 3 int (dimensions x,y,z)
  Ny*Nz listes de Nx 3-char (à définir, cf parser affichage)

- scoring (TX)
  nombre de coups
  flag succès
  {actions: float, success: bool}


