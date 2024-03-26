from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.list import ListView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import authentication, permissions
from django.contrib.auth.models import User

from .models import Map, Game, Stage, Team

def index(request):
    teams = Team.objects.filter(user__last_name="team")
    return render(request, 'index.html', {'teams': teams})

def show_game(request, pk):
    game = Game.objects.get(pk=pk)
    return HttpResponse(game.map.map_data+'\n'+game.moves + '\nEND OK 8', content_type="text/plain")

class ListGamesView(ListView):
    model = Game

    def get_queryset(self):
        return Game.objects.all().order_by('-completed_at')

class TokenTestView(APIView):

    def post(self, request):
        return Response({'message': 'Token is valid'})

class NewMapView(APIView):

    def post(self, request):
        map_data = request.data.get('map')
        stage_endpoint = request.data.get('stage')
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
        map_obj = Map(map_data=map_data, proposed_by=request.user)
        valid_map, errors = map_obj.validate()
        if valid_map:
            map_obj.save()

            if stage_endpoint is not None:
                stage.maps.add(map_obj)
            return Response({'status': 'success'})
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
                    {'status': 'error', 'message': f'No stage named {stage_name} found'},
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
        return Response({'status': 'success', 'game_id': game.id})

class ProposeSolutionView(APIView):
    def post(self, request, game_id=None):
        moves = request.data.get('moves')
        if game_id is None or moves is None:
            return Response(
                {'status': 'error', 'message': 'game_id and moves are required'},
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

    def post(self, request):
        referee = request.user
        stage_id = request.data.get('stage_id')
        game_id = request.data.get('game_id')
        score = request.data.get('score')

        if score is not None and game_id is not None:
            pass
        else:
            # return a game to score
            if stage_id is not None:
                try:
                    stage = Stage.objects.get(stage_id=stage_id)
                except Stage.DoesNotExist:
                    return Response(
                        {'status': 'error', 'message': f'No stage named {stage_id} found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
               # check wether a game in the stage without score given by the referee exist


            game = Game.objects.filter(map__proposed_by=referee, finished=True).order_by('?').first()
            return Response({'game_id': game.id, 'map': game.map.map_data, 'moves': game.moves})
