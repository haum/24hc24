#! /usr/bin/env python
# -*- coding:utf8 -*-
#
# 24hc24.py
#
# Copyright © 2024 Mathieu Gaborit (matael) <mathieu@matael.org>
#
# Licensed under the "THE BEER-WARE LICENSE" (Revision 42):
# Mathieu (matael) Gaborit wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a beer or coffee in return
#

from django import template
from serv.models import Team
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def displayname(obj):
    if isinstance(obj, User):
        teamobj = Team.objects.get(user=obj)
    else:
        teamobj = obj
    return teamobj.name if teamobj.name else teamobj.user.username
