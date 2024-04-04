from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import authentication, permissions
from django.contrib.auth.models import User

from .models import Map, Game, Stage, Team, Score

def index(request):
    teams = Team.objects.all()
    return render(request, 'index.html', {'teams': teams})

def show_game(request, pk):
    game = Game.objects.get(pk=pk)
    return HttpResponse(game.map.map_data+'\n'+game.moves + f'\nEND {"OK" if game.victory else "NOK"} {game.reference_score}\n', content_type="text/plain")

def show_map(request, pk):
    map = Map.objects.get(pk=pk)
    return HttpResponse(map.map_data+'\nEND NOK 0', content_type="text/plain")

class TeamView(DetailView):
    model = User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.get(user=self.object)
        context['games_player'] = Game.objects.filter(player=self.object).order_by('-completed_at')
        games_on_proposed_maps = Game.objects.filter(map__proposed_by=self.object).order_by('-completed_at')
        scores = {_.game.id: _.score for _ in Score.objects.filter(referee=self.object)}
        context['games_game'] = [(game, scores.get(game.id, None)) for game in games_on_proposed_maps]

        return context

class ListGamesView(ListView):
    model = Game

    def get_queryset(self):
        return Game.objects.all().order_by('-completed_at')

class ListMapsView(ListView):
    model = Map

class TokenTestView(APIView):

    def post(self, request):
        return Response({'status': 'success', 'message': 'Token is valid'})

class NewMapView(APIView):

    def post(self, request, stage_endpoint=None):
        map_data = request.data.get('map')
        if stage_endpoint is not None:
            try:
                stage = Stage.objects.get(endpoint=stage_endpoint)
            except Stage.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': f'No stage named {stage_endpoint} found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if not stage.running:
                return Response(
                    {'status': 'error', 'message': f'Stage {stage_endpoint} is not running'},
                    status=status.HTTP_403_FORBIDDEN
                )
        if map_data is None:
            return Response(
                {'status': 'error', 'message': 'No map data found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if stage_endpoint is not None:
            if stage.number_of_maps > 0 and Map.objects.filter(stage=stage, proposed_by=request.user).count() >= stage.number_of_maps:
                return Response(
                    {'status': 'error', 'message': f'No more maps allowed for stage {stage_endpoint}'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if stage.end_of_map_submission is not None and stage.end_of_map_submission < timezone.now():
                return Response(
                    {'status': 'error', 'message': f'End of map submission for stage {stage_endpoint} has passed'},
                    status=status.HTTP_403_FORBIDDEN
                )
        map_obj = Map(map_data=map_data, proposed_by=request.user)
        valid_map, errors = map_obj.validate()
        if valid_map:
            map_obj.save()

            if stage_endpoint is not None:
                stage.maps.add(map_obj)
            return Response({'status': 'success', 'message': 'Map created'})
        else:
            return Response(
                {'status': 'error', 'message': 'Invalid map', 'map_error': errors},
                status=status.HTTP_400_BAD_REQUEST
            )

class NewGameView(APIView):

    def get(self, request, stage_endpoint=None):
        if stage_endpoint is not None:
            try:
                stage = Stage.objects.get(endpoint=stage_endpoint)
            except Stage.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': f'No stage named {stage_endpoint} found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not stage.running:
                return Response(
                    {'status': 'error', 'message': f'Stage {stage_endpoint} is not running'},
                    status=status.HTTP_403_FORBIDDEN
                )
            played_maps = set(Game.objects.filter(player=request.user, stage=stage).values_list('map', flat=True))
            all_maps_from_stage = set(stage.maps.values_list('id', flat=True))
            remaining_maps = all_maps_from_stage.difference(played_maps)
            if not remaining_maps:
                return Response(
                    {'status': 'error', 'message': 'No more maps to play'},
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )
            proposed_map = Map.objects.filter(id__in=remaining_maps).order_by('?').first()
            game = Game(
                map=proposed_map,
                stage=stage,
                player=request.user
            )
            game.save()

        else:
            proposed_map = Map.objects.order_by('?').first()
            game = Game(
                map=proposed_map,
                player=request.user
            )
            game.save()
        return Response({'status': 'success', 'game_id': game.id, 'map_data': game.map.map_data})

class ProposeSolutionView(APIView):
    def post(self, request, game_id):
        moves = request.data.get('moves')
        if moves is None:
            return Response(
                {'status': 'error', 'message': 'Moves are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return Response(
                {'status': 'error', 'message': f'No game with id {game_id} found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if game.player != request.user:
            return Response(
                {'status': 'error', 'message': 'You are not allowed to propose a solution for this game'},
                status=status.HTTP_403_FORBIDDEN
            )
        game.moves = moves
        game.finished = True
        game.save()
        analysis_result = game.compute_reference_score()
        return Response({'status': 'success', 'reference_score': analysis_result.moves,
                         'message': analysis_result.msg, 'victory': analysis_result.ok})

class ScoreGameView(APIView):

    def get(self, request, stage_endpoint=None):
        referee = request.user
        if stage_endpoint is not None:
            try:
                stage = Stage.objects.get(endpoint=stage_endpoint)
            except Stage.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': f'No stage named {stage_endpoint} found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            game = Game.objects.filter(map__proposed_by=referee, stage=stage, score=None, finished=True).order_by('?').first()
            return Response({'status': 'success', 'game_id': game.id, 'map_data': game.map.map_data, 'moves': game.moves, 'stage': stage.endpoint})
        else:
            game = Game.objects.filter(map__proposed_by=referee, score=None, finished=True).order_by('?').first()
            return Response({'status': 'success', 'game_id': game.id, 'map_data': game.map.map_data, 'moves': game.moves})

    def post(self, request, stage_endpoint=None):
        referee = request.user
        game_id = request.data.get('game_id')
        score = float(request.data.get('score'))

        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return Response(
                {'status': 'error', 'message': f'No game with id {game_id} found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if game.map.proposed_by != referee:
            return Response(
                {'status': 'error', 'message': 'You are not allowed to score this game'},
                status=status.HTTP_403_FORBIDDEN
            )

        if game.score_set.count():
            return Response(
                {'status': 'error', 'message': 'This game has already been scored'},
                status=status.HTTP_403_FORBIDDEN
            )

        if stage_endpoint is not None:
            try:
                stage = Stage.objects.get(endpoint=stage_endpoint)
            except Stage.DoesNotExist:
                return Response(
                    {'status': 'error', 'message': f'No stage named {stage_endpoint} found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if game.stage != stage:
                return Response(
                    {'status': 'error', 'message': f'This game does not belong to stage {stage_endpoint}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        score = Score(game=game, referee=referee, score=score)
        score.save()
        return Response({'status': 'success', 'message': 'Score saved'})

