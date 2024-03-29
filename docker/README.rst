Docker
======

Create image
------------

`docker build -t haum/24hc24-django .`

Run image
---------

Launch update script that will launch the service.

`./update-on-server.sh`

Note: use `ssh -A` to connect to server so that git can pull private repo + be in docker group to start the app
