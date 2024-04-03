Protocole
=========

Toutes les communications se font avec le serveur du HAUM, et se fera avec une interface REST/JSON.
Les programmes seront exécutés sur les machines des participants.

..

   "Le Jeu"
   --------

   Envoyer la carte
   """"""""""""""""

   Valider les déplacements
   """"""""""""""""""""""""

   "Le Joueur"
   -----------

   Récupérer la carte
   """"""""""""""""""

   Envoyer les déplacements
   """"""""""""""""""""""""

Informations Générales
----------------------

Les requètes sont à envoyer en POST ou GET avec une payload JSON. Les réponses sont
également en JSON. Le token d'authentification est à envoyer dans le header
``Authorization`` de la requète sous la forme :

```
Authorization: Token <token>
```

Le code HTTP vous informe sur le succès ou non de la requète. La payload JSON retournée
contient également un rappel du statut dans le champs ``status`` (soit ``success`` soit
``error``) ainsi qu'un message dans le champs ``message``. Ces informations vous
permettent de débugger votre code.

POST /api/tokentest
-------------------

Infos
*****

- Payload: ``{}``

Retours possibles
*****************

- 200: ``{'message': 'Token is valid'}``

POST /api/map/new/[stage_endpoint]
----------------------------------

Infos
*****

- GET params: 'stage_endpoint' (facultatif)
- payload: ``{'map': string multiligne}``

Retours possibles
*****************

- 200 OK: ``{'message': 'Map created'}``
- 404 NOT FOUND: ``{'message': 'No stage named <stage_endpoint> found'}``
- 403 FORBIDDEN: ``{'message': 'Stage <stage_endpoint> is not running'}``
- 400 BAD REQUEST: ``{'message': 'No map data found'}``
- 400 BAD REQUEST: ``{'message': 'Invalid map', 'map_error': str}``


GET /api/game/new/[stage_endpoint]
----------------------------------

Infos
*****

- GET params: 'stage_endpoint' (facultatif)

Retours possibles
*****************

- 404 NOT FOUND: ``{'message': 'No stage named <stage_endpoint> found'}``
- 403 FORBIDDEN: ``{'message': 'Stage <stage_endpoint> is not running'}``
- 402 PAYMENT REQUIRED: ``{'message': 'No more maps to play'}``
- 200 OK: ``{'game_id': int, 'map_data': string multiligne}``

POST /api/game/[game_id]/solve
------------------------------

Infos
*****

- GET params: 'game_id' (int, obligatoire)
- payload: ``{'moves': string multiligne}``

Retours possibles
*****************

- 400 BAD REQUEST: ``{'message': 'Moves are required'}``
- 404 NOT FOUND: ``{'message': 'No game with id <game_id> found'}``
- 403 FORBIDDEN: ``{'message': 'You are not allowed to propose a solution for this game'}``
- 200 OK: ``{'message': str, 'victory': bool, 'reference_score': float}``

GET /api/score/[stage_endpoint]
-------------------------------

Infos
*****

- GET params: 'stage_endpoint' (facultatif)

Retours possibles
*****************

- 404 NOT FOUND: ``{'message': 'No stage named <stage_endpoint> found'}``
- 200 OK: ``{'game_id': int, 'map_data': string multiligne, 'moves': string multiligne}``

POST /api/score/[stage_endpoint]
--------------------------------

Infos
*****

- GET params: 'stage_endpoint' (facultatif)
- payload: ``{'game_id': int, 'score': float}``

Retours possibles
*****************

- 404 NOT FOUND: ``{'message': 'No stage named <stage_endpoint> found'}``
- 400 BAD REQUEST: ``{'message': 'This game does not belong to stage <stage_endpoint>'}``
- 404 NOT FOUND: ``{'message': 'No game with id <game_id> found'}``
- 403 FORBIDDEN: ``{'message': 'You are not allowed to score this game'}``
- 403 FORBIDDEN: ``{'message': 'This game has already been scored'}``
- 200 OK: ``{'message': 'Score saved'}``

