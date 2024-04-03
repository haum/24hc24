Règles du jeu
=============

Blocs
-----

Il existe différents (8) types de blocs :

 - Les destinations (Noir)
 - Les astéroïdes (Bleu)
 - Les nébuleuses (Jaune)
 - Les nuages magnétiques (Gris)
 - 4 checkpoints (Vert)

A quoi s'ajoute l'espace (Transparent) vu comme une absence de bloc.

.. note:: Puisque l'idée vous a bien plu l'an dernier, le codage de la carte et de son contenu est à retrouver par retro-ingénierie à l'aide des exemples disponibles sur le serveur.

L'espace
""""""""

On peut s'y déplacer librement.

Les destinations
""""""""""""""""

Atteindre un bloc de destnation termine la partie.

Les astéroïdes
""""""""""""""

Tout contact avec ce type de bloc ne donnera qu'un seul résultat : La fin prématurée de la mission.

Les nébuleuses
""""""""""""""

Lorsque le vaisseau effectue une action à l'intérieur d'une nébuleuse, il ne pourra que ralentir jusqu'a atteindre sa vitesse minimale.

Les nuages magnétiques
""""""""""""""""""""""

La seule action possible pour un vaisseau pénétrant dans un nuage magnétique est une accélération nulle.

Les checkpoints
"""""""""""""""

Si un ou plusieurs checkpoints existent sur la carte, ils doivent être traversés dans l'ordre avant d'atteindre la destination.

Accélération
------------

Le vaisseau se commande en indiquant les vecteurs d'accélération.
L'accélération est un vecteur d'entier dont chaque composante va de -1 à +1.

.. note:: Exemple : Le vaisseau est en position (0,0,0) et effectue une accélération de (1,0,0). Il se retrouve en position (1,0,0). Il effectue ensuite une accélération de (0,1,0), il se retrouve donc en (2,1,0).

Collision
---------

Coups
-----
