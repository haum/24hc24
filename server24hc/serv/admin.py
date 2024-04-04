from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Team, Game, Map, Stage, Score


class StagelistFilter(admin.SimpleListFilter):
    title = 'stage'
    parameter_name = 'stage'

    def lookups(self, request, model_admin):
        return [(s.id, s.endpoint) for s in Stage.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(stage=self.value())
        return queryset

class TeamRefereeFilter(admin.SimpleListFilter):
    title = 'referee'
    parameter_name = 'referee'

    def lookups(self, request, model_admin):
        return [(s.user.id, s.user.username) for s in Team.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(referee=self.value())
        return queryset

class TeamPlayerFilter(admin.SimpleListFilter):
    title = 'player'
    parameter_name = 'player'

    def lookups(self, request, model_admin):
        return [(s.user.id, s.user.username) for s in Team.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(player=self.value())
        return queryset

class TeamAdmin(admin.ModelAdmin):
    list_display = ('user', 'games_played', 'score_player', 'score_game', 'score_full')


class MapAdmin(admin.ModelAdmin):
    list_display = ('id', 'proposed_by', 'size', 'in_stage', 'proposed_at', 'impossible')
    list_filter = ('proposed_by', StagelistFilter)


class ScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'on_map', 'player', 'referee', 'valid')
    list_filter = (TeamRefereeFilter, 'valid')

    def on_map(self, obj):
        url = reverse('admin:serv_map_change', args=[obj.game.map.id])
        return mark_safe(f"<a href='{url}'>Map #{obj.game.map.id}</a>")
    on_map.allow_tags = True

    def player(self, obj):
        return obj.game.player.username


class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'on_map', 'stage', 'victory', 'finished', 'completed_at', 'reference_score')
    list_filter = (TeamPlayerFilter, 'stage', 'victory', 'finished')

    def player(self, obj):
        return obj.player.username

    def on_map(self, obj):
        url = reverse('admin:serv_map_change', args=[obj.map.id])
        return mark_safe(f"<a href='{url}'>Map #{obj.map.id}</a>")
    on_map.allow_tags = True

    def completed_at(self, obj):
        return obj.completed_at


class StageAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'number_of_maps', 'end_of_map_submission',
                    'maps_submitted', 'all_maps_submitted', 'all_games_played', 'running', 'dev')
    list_filter = ('dev', 'running')
    filter_horizontal = ('maps',)

    def maps_submitted(self, obj):
        return obj.maps.count()

    def all_maps_submitted(self, obj):
        return obj.number_of_maps <= 0 or obj.number_of_maps*Team.objects.all().count() == obj.maps.count()
    all_maps_submitted.boolean = True

    def all_games_played(self, obj):
        return obj.maps.count()*Team.objects.all().count() == obj.game_set.count()
    all_games_played.boolean = True


admin.site.register(Team, TeamAdmin)
admin.site.register(Map, MapAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Stage, StageAdmin)
