#!/bin/bash
sudo docker stop 24hc24_nginx_doc
sudo docker run --rm --name 24hc24_nginx_doc --mount type=bind,source=/var/www/odysseehaumere.haum.org/24hc24/,target=/usr/share/nginx/html,readonly -p 8099:80 -d nginx

