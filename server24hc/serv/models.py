from django.db import models
from django.contrib.auth.models import User

from .maputils import Map as MapUtils

class Team(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    @property
    def games_played(self):
        return Game.objects.filter(player=self.user, finished=True).count()

    @property
    def score_player(self):
        # implement
        return 0

    @property
    def score_game(self):
        # implement
        return 0

    @property
    def score_full(self):
        # implement
        return self.score_player + self.score_game

class Map(models.Model):
    map_data = models.TextField()
    proposed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    proposed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.proposed_by.username + " - " + str(self.proposed_at)

    def validate(self):
        errors = MapUtils(self.map_data).find_error()
        return errors is None, errors

class Stage(models.Model):
    maps = models.ManyToManyField(Map)
    endpoint = models.CharField(max_length=100, unique=True)
    time_limit = models.IntegerField(default=None, null=True, blank=True, help_text="Time limit in seconds")
    running = models.BooleanField(default=False)

    def __str__(self):
        return self.endpoint

class Game(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    moves = models.TextField(default="")
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, blank=True, null=True, default=None)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, default=None)
    finished = models.BooleanField(default=False)
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player')
    reference_score = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.finished and self.reference_score is None:
            self.compute_reference_score()
        super().save(*args, **kwargs)

    def compute_reference_score(self):
        if self.finished:
            m = MapUtils(self.map.map_data)
            analysis_result = m.analyze_path(self.moves)
            self.reference_score = analysis_result.moves
            return analysis_result
        else:
            return None

    def __str__(self):
        return f"Game {self.id} by {self.player.username} on map {self.map.id}"

class Score(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score = models.IntegerField()
    referee = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.referee.username + " - " + str(self.score)
