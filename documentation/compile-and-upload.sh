#!/bin/bash

make html && rsync -ahvPzz --no-group --no-perms --no-times ../documentation-build/html/ haum.org:/var/www/odysseehaumere.haum.org/24hc24/doc
