from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from .maputils import Map as MapUtils
from .bruteforce_solve import bruteforce_solve

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    position = models.CharField(max_length=250, blank=True, null=True)
    student = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score_player = models.FloatField(default=0)
    score_game = models.FloatField(default=0)

    @property
    def games_played(self):
        return Game.objects.filter(player=self.user, finished=True).count()

    @property
    def games_scored(self):
        return Score.objects.filter(referee=self.user).count()

    def compute_score_player(self):
        score = 0
        for s in Stage.objects.filter(dev=False):
            for m in s.maps.all():
                g = Game.objects.filter(map=m, finished=True, stage=s, player=self.user).order_by('-completed_at').first()
                worst_score = Game.objects.filter(map=m, finished=True, victory=True, stage=s).order_by('-reference_score').first().reference_score
                best_scored_game = Game.objects.filter(map=m, finished=True, victory=True, stage=s).order_by('reference_score').first()
                if g is None:
                    # The team didn't play => 10*worst_score
                    if worst_score is not None:
                        score += 10*worst_score
                    else: # If no game has been played on the map => neutralized.
                        score += 0
                if best_scored_game is not None:
                    best_score = best_scored_game.reference_score
                    current_player_score = g.reference_score
                    score += current_player_score - best_score
                    # if the team won => golf score
                    if not game.victory: # if the team lost => golf score +  2*golf score of the worst game
                        score += 2*(worst_score - best_score)
        return score

    def compute_score_game(self):
        score = 0
        for s in Stage.objects.filter(dev=False):
            if s.number_of_maps > 0:
                # 100 points for each missing map
                score += 10*(s.number_of_maps - s.maps.filter(proposed_by=self.user).count())
                # 20 points for each game played and valid but that hasn't been scored
                score += 20*(Game.objects.filter(stage=s, map__proposed_by=self.user).exclude(moves='').count() - Score.objects.filter(game__map__proposed_by=self.user, game__stage=s).count())
            for m in s.maps.filter(proposed_by=self.user):
                # +1 point per winning game on the map
                winning_games = Game.objects.filter(map=m, finished=True, victory=True, stage=s).count()
                score += winning_games

                # +10 points per map with at least one wrongly scored game
                wrongly_scored_games = Score.objects.filter(game__map=m, game__stage=s, referee=self.user, valid=False).exclude(game__moves='').count()
                score += 10*(wrongly_scored_games > 0)

                # 20point per game on a map nobody managed to solve (Games *must* provide possible maps)
                number_of_games = Game.objects.filter(map=m, stage=s).count()
                if m.impossible is not None and m.impossible:
                    score += number_of_games*20

        return score

    @property
    def score_full(self):
        return self.score_player + self.score_game

class Map(models.Model):
    map_data = models.TextField()
    proposed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    proposed_at = models.DateTimeField(auto_now_add=True)
    impossible = models.BooleanField(default=None, blank=True, null=True)

    @property
    def size(self):
        return 'x'.join(self.map_data.split('\n')[0].split(' ')[1:]).rstrip()

    @property
    def in_stage(self):
        return [s.endpoint for s in Stage.objects.filter(maps=self).distinct()]

    def __str__(self):
        return "#"+ str(self.id) + " - " + self.size+' map by team ' + self.proposed_by.username

    def validate(self):
        errors = MapUtils(self.map_data).find_error()
        return errors is None, errors

class Stage(models.Model):
    maps = models.ManyToManyField(Map, null=True, blank=True)
    endpoint = models.CharField(max_length=100, unique=True)
    end_of_map_submission = models.DateTimeField(default=None, blank=True, null=True)
    end_of_moves_submission = models.DateTimeField(default=None, blank=True, null=True)
    end_of_score_submission = models.DateTimeField(default=None, blank=True, null=True)
    number_of_maps = models.IntegerField(default=-1)
    running = models.BooleanField(default=False)
    dev = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.running:
            games = Game.objects.filter(stage=self, finished=False).update(finished=True, victory=False)
            for m in self.maps.filter(impossible=None):
                if Game.objects.filter(map=m, stage=self, victory=True).count() != 0:
                    m.impossible = False
                else:
                    m.impossible = True
                m.save()

    def __str__(self):
        return self.endpoint

class Game(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    moves = models.TextField(default="")
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, blank=True, null=True, default=None)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, default=None)
    finished = models.BooleanField(default=False)
    victory = models.BooleanField(default=False)
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player')
    analysis_message = models.TextField(null=True, blank=True)
    reference_score = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.finished and self.reference_score is None:
            m = MapUtils(self.map.map_data)
            analysis_result = m.analyze_path(self.moves)
            self.analysis_message = analysis_result.msg
            self.reference_score = analysis_result.moves
            self.victory = analysis_result.ok
        if self.finished and self.completed_at is None:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Game {self.id} by {self.player.username} on map {self.map.id}"

class Score(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score = models.FloatField()
    referee = models.ForeignKey(User, on_delete=models.CASCADE)
    valid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.game.reference_score == self.score or abs(self.score - self.game.reference_score)/self.game.reference_score < 0.01:
            self.valid = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.referee.username + " - " + str(self.score)
