#!/bin/sh

sudo docker stop haum-24hc24-django
git pull --ff-only
sudo docker run --rm -v /var/www/odysseehaumere.haum.org/:/persist haum/24hc24-django sh -c 'python3 /persist/24hc24/server24hc/manage.py migrate'
sudo docker run --rm -d -p 127.0.0.1:83:8000 --network=24hc24 -v /var/www/odysseehaumere.haum.org/:/persist --name haum-24hc24-django haum/24hc24-django /persist/24hc24/docker/app.sh
