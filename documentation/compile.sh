#!/bin/bash

make html
rsync -ahvgP --no-g --no-perms --no-times ../documentation-build/html/ haum.org:/var/www/odysseehaumere.haum.org/24hc24/doc
