from django.contrib import admin

from .models import Team, Game, Map, Stage, Score

admin.site.register(Team)
admin.site.register(Game)
admin.site.register(Map)
admin.site.register(Stage)
admin.site.register(Score)
