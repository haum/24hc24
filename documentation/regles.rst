Règles du jeu
=============

Blocs
-----

Il existe 8 différents types de blocs :

 - Les destinations (Noir)
 - Les astéroïdes (Bleu)
 - Les nébuleuses (Jaune)
 - Les nuages magnétiques (Gris)
 - 4 types de checkpoints (Vert)

À ces blocs s'ajoute évidemment l'espace (Transparent), qui peut être vu comme une absence de bloc.

L'espace
""""""""

On peut s'y déplacer librement.

Destinations
""""""""""""

Atteindre un bloc de destination termine la partie.

Astéroïdes
""""""""""

Tout contact avec ce type de bloc ne donnera qu'un seul résultat : La fin prématurée de la mission.

Nébuleuses
""""""""""

Lorsque le vaisseau effectue une action à l'intérieur d'une nébuleuse, il ne pourra que ralentir jusqu'à atteindre sa vitesse minimale (non nulle).

Nuages magnétiques
""""""""""""""""""

La seule action possible pour un vaisseau se trouvant dans un nuage magnétique est une accélération nulle.

Checkpoints
"""""""""""

Les checkpoints sont des points de collecte à traverser impérativement avant d'atteindre la destination. 
Ils sont organisés en étapes (de 0 à 4 possibles par carte) qu'il faut valider dans l'ordre en traversant un des checkpoints de l'étape concernée. Passer par un checkpoint d'une étape passée ou future est ignoré. 

Sur une carte, les étapes sont forcément ordonnées, sans saut dans la numérotation.

Cartes
------

Les cartes sont de la forme qui suit :

::

    MAP 3 6 2
    AAA AAA AAA
    AAA AAA AAA
    AAA AAA AAA
    AAA AAA AAA
    AAA AAA AAA
    Ae/ AAA AAA

    AAA AAA AAA
    AAA AAA AAA
    AAA AAA AAA
    AAA AAA AAA
    AAA AAA AAA
    AAA AAA AAA
    ENDMAP
    START 2 0 1

.. note:: Puisque l'idée vous a bien plu l'an dernier, le codage de la carte et de son contenu est à retrouver par retro-ingénierie à l'aide des exemples disponibles sur le serveur.

Accélération
------------

Le vaisseau se commande en indiquant les vecteurs d'accélération.
L'accélération est un vecteur d'entier dont chaque composante va de -1 à +1.

.. note:: Exemple : Le vaisseau est en position (0,0,0) et effectue une accélération de (1,0,0). Il se retrouve en position (1,0,0). Il effectue ensuite une accélération de (0,1,0), il se retrouve donc en (2,1,0).

Exemple de liste d'accélération à envoyer au serveur :
::

    ACC 0 1 0
    ACC 1 0 0
    ACC 0 -1 0
    ACC 1 0 0
    ACC -1 1 1
    ACC -1 -1 -1
    ACC -1 0 0
    ACC -1 0 0

Coups
-----

Le nombre de coups joués est le nombre d'accélérations exécutées par le serveur.
Si le mouvement se termine prématurément (collision ou franchissement de la destination par exemple), il est compté au prorata du déplacement prévu.
