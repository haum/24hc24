import uuid
import pytest
import random

from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.authtoken.models import Token
from .models import Team, Map, Game, Stage, Score

@pytest.fixture
def test_password():
   return 'strong-test-pass'

@pytest.fixture
def create_user(db, django_user_model, test_password):
   def make_user(**kwargs):
       kwargs['password'] = test_password
       if 'username' not in kwargs:
           kwargs['username'] = str(uuid.uuid4())
       return django_user_model.objects.create_user(**kwargs)
   return make_user

@pytest.fixture
def get_or_create_token(db, create_user):
    user = create_user()
    token, created = Token.objects.get_or_create(user=user)
    return token

@pytest.fixture()
def api_client():
   from rest_framework.test import APIClient
   return APIClient()

@pytest.fixture
def simple_map_str():
    return 'MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA A//\nENDMAP\nSTART 0 0 0'

@pytest.fixture
def invalid_map_str_no_arrival():
    # todo add a start and stop to it
    return 'MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA AAA\nENDMAP\nSTART 0 0 0'


def test_assess_token(api_client, create_user, get_or_create_token):
    token = get_or_create_token

    api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    response = api_client.post('/api/tokentest')
    assert response.status_code == 200

def test_assess_token_fail(api_client, create_user, get_or_create_token):
    token = get_or_create_token

    api_client.credentials(HTTP_AUTHORIZATION='Token ' + 'test phony')
    response = api_client.post('/api/tokentest')
    assert response.status_code == 401

class TestMapSubmission:
    @pytest.fixture
    def stage(self):
        stage = Stage(endpoint='test')
        stage.save()
        yield stage
        stage.delete()

    @pytest.fixture
    def stage_running(self):
        stage = Stage(endpoint='test', running=True)
        stage.save()
        yield stage
        stage.delete()

    def test_new_map(self, api_client, get_or_create_token, simple_map_str):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/map/new', {'map': simple_map_str})
        assert response.status_code == 200
        db_map = Map.objects.all().last()
        assert db_map.map_data == simple_map_str
        assert db_map.proposed_by == token.user

    def test_new_map_no_arrival(self, api_client, get_or_create_token, invalid_map_str_no_arrival):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/map/new', {'map': invalid_map_str_no_arrival})
        assert response.status_code == 400
        assert response.data['message'] == 'Invalid map'
        assert response.data['map_error'] == 'No arrival'

    def test_no_map_data(self, api_client, get_or_create_token):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/map/new', {})
        assert response.status_code == 400
        assert response.data['message'] == 'No map data found'

    def test_add_map_to_running_stage(self, api_client, get_or_create_token, simple_map_str, stage_running):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/map/new/{stage_running.endpoint}', {'map': simple_map_str})
        assert response.status_code == 200
        db_map = Map.objects.all().last()
        assert db_map.map_data == simple_map_str
        assert db_map.proposed_by == token.user
        assert stage_running.maps.count() == 1

    def test_add_map_to_non_running_stage(self, api_client, get_or_create_token, simple_map_str, stage):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/map/new/{stage.endpoint}', {'map': simple_map_str})
        assert response.status_code == 403

    def test_add_map_to_non_exisitent_stage(self, api_client, get_or_create_token, simple_map_str):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/map/new/phony', {'map': simple_map_str})
        assert response.status_code == 404

    def test_add_too_many_maps(self, api_client, get_or_create_token, simple_map_str, stage_running):
        stage_running.number_of_maps = 1
        stage_running.save()

        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/map/new/{stage_running.endpoint}', {'map': simple_map_str})
        assert response.status_code == 200
        response = api_client.post(f'/api/map/new/{stage_running.endpoint}', {'map': simple_map_str})
        assert response.status_code == 403
        assert response.data['message'] == f'No more maps allowed for stage {stage_running.endpoint}'

    def test_out_of_time_submission(self, api_client, get_or_create_token, simple_map_str, stage_running):
        stage_running.end_of_map_submission = timezone.now() - timedelta(days=1)
        stage_running.save()

        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/map/new/{stage_running.endpoint}', {'map': simple_map_str})
        assert response.status_code == 403
        assert response.data['message'] == f'End of map submission for stage {stage_running.endpoint} has passed'

class TestGameRequestMechanics:

    @pytest.fixture(autouse=True)
    def setup(self, create_user):
        self.user = create_user()
        self.the_map = Map(map_data='MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA AAA\nENDMAP\nSTART 0 0 0', proposed_by=self.user)
        self.the_map.save()
        yield 'setup done'
        self.the_map.delete()
        self.user.delete()

    @pytest.fixture
    def stage_no_map(self):
        stage = Stage(endpoint='test')
        stage.save()
        yield stage
        stage.delete()

    @pytest.fixture
    def stage_with_map(self):
        stage = Stage(endpoint='test', running=True)
        stage.save()
        stage.maps.add(self.the_map)
        yield stage
        stage.delete()

    def test_new_game_nostage(self, api_client, get_or_create_token):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.get('/api/game/new')
        assert response.status_code == 200, response.data['message']
        game = Game.objects.get(player=token.user)
        assert game.map.proposed_by == self.user
        assert game.map.proposed_by != token.user
        assert game.map.map_data == self.the_map.map_data

    def test_new_game_stage_not_running(self, api_client, get_or_create_token, stage_no_map):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.get(f'/api/game/new/{stage_no_map.endpoint}')
        assert response.status_code == 403, response.data

    def test_new_game_stage_inexistent_stage(self, api_client, get_or_create_token):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.get('/api/game/new/phony_map')
        assert response.status_code == 404, response.data
        assert response.data['message'] == 'No stage named phony_map found'

    def test_new_game_stage_nomap_left(self, api_client, get_or_create_token, stage_no_map):
        stage_no_map.running = True
        stage_no_map.save()
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.get(f'/api/game/new/{stage_no_map.endpoint}')
        assert response.status_code == 402, response.data

    def test_new_game_stage(self, api_client, get_or_create_token, stage_with_map):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.get(f'/api/game/new/{stage_with_map.endpoint}')
        assert response.status_code == 200, response.data
        game = Game.objects.get(player=token.user)
        assert game.map.proposed_by == self.user
        assert game.map.proposed_by != token.user
        assert game.map.map_data == self.the_map.map_data

    def test_new_game_stage_exhausted(self, api_client, get_or_create_token, stage_with_map):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.get(f'/api/game/new/{stage_with_map.endpoint}')
        response = api_client.get(f'/api/game/new/{stage_with_map.endpoint}')
        assert response.status_code == 402, response.data

class TestPlayMechanics:
    @pytest.fixture
    def setup_maps(self, create_user):
        self.user = create_user()
        self.maps = []
        self.maps.append(Map(map_data="""MAP 10 8 5
BMz AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA BP/ AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA CP/ C/9 AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA EVV FVV GVV HVV AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA D// AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AVV AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA

AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
AAA AAA AAA AAA AAA AAA AAA AAA AAA AAA
ENDMAP
START 2 1 2""", proposed_by=self.user))
        self.maps.append(Map(map_data='MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA AAA\nENDMAP\nSTART 0 0 0', proposed_by=self.user))
        self.maps.append(Map(map_data='MAP 2 2 1\nAAA AAA\nAAA AAA\nAAA AAA\nENDMAP\nSTART 0 0 0', proposed_by=self.user))
        for _ in self.maps:
            _.save()
        yield 'setup done'
        for _ in self.maps:
            _.delete()
        self.user.delete()

    @pytest.fixture
    def first_map_solution(self):
        return """ACC 0 1 0
ACC 1 0 0
ACC 0 -1 0
ACC 1 0 0
ACC -1 1 1
ACC -1 -1 -1
ACC -1 0 0
ACC -1 0 0"""

    @pytest.fixture
    def setup_game_randommap(self, get_or_create_token, setup_maps):
        self.player_user = get_or_create_token.user
        self.game = Game(map=random.choice(self.maps), player=self.player_user)
        self.game.save()
        yield 'setup done'
        self.game.delete()
        self.player_user.delete()

    @pytest.fixture
    def setup_game_firstmap(self, get_or_create_token, setup_maps):
        self.player_user = get_or_create_token.user
        self.game = Game(map=self.maps[0], player=self.player_user)
        self.game.save()
        yield 'setup done'
        self.game.delete()
        self.player_user.delete()

    def test_valid_solution(self, api_client, setup_game_firstmap, first_map_solution):
        token = Token.objects.get(user=self.player_user)
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/game/{self.game.id}/solve', {'moves': first_map_solution})
        assert response.status_code == 200, response.data
        assert response.data['victory']
        db_game = Game.objects.get(pk=self.game.id)
        assert db_game.finished
        assert db_game.moves == first_map_solution
        assert db_game.reference_score == pytest.approx(7.416666, rel=1e-6)

    def test_double_submission(self, api_client, setup_game_firstmap, first_map_solution):
        token = Token.objects.get(user=self.player_user)
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/game/{self.game.id}/solve', {'moves': first_map_solution})
        assert response.status_code == 200, response.data
        assert response.data['victory']
        db_game = Game.objects.get(pk=self.game.id)
        assert db_game.finished
        assert db_game.moves == first_map_solution
        assert db_game.reference_score == pytest.approx(7.416666, rel=1e-6)
        response = api_client.post(f'/api/game/{self.game.id}/solve', {'moves': first_map_solution})
        assert response.status_code == 403, response.data
        assert response.data['message'] == 'This game has already been solved'

    def test_inexistent_game(self, api_client, setup_game_firstmap, first_map_solution):
        token = Token.objects.get(user=self.player_user)
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/game/999/solve', {'moves': first_map_solution})
        assert response.status_code == 404, response.data
        assert response.data['message'] == 'No game with id 999 found'

    def test_incorrect_payload(self, api_client, setup_game_firstmap, first_map_solution):
        token = Token.objects.get(user=self.player_user)
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/game/{self.game.id}/solve', {})
        assert response.status_code == 400, response.data
        assert response.data['message'] == 'Moves are required'

    def test_incorrect_player(self, api_client, setup_game_firstmap, first_map_solution, create_user):
        new_user = create_user()
        token, _ = Token.objects.get_or_create(user=new_user)
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/game/{self.game.id}/solve', {'moves': first_map_solution})
        assert response.status_code == 403, response.data
        assert response.data['message'] == 'You are not allowed to propose a solution for this game'

class TestScoringMechanics:
    @pytest.fixture
    def setup_finished_game(self, create_user):
        self.referee = create_user()
        self.player = create_user()
        self.referee_token, _ = Token.objects.get_or_create(user=self.referee)
        self.player_token, _  = Token.objects.get_or_create(user=self.player)
        self.map = Map(map_data='MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA A//\nENDMAP\nSTART 0 0 0', proposed_by=self.referee)
        self.map.save()
        self.game = Game(map=self.map, player=self.player, finished=True, moves='ACC 1 1 1')
        self.game.save()

    @pytest.fixture
    def setup_finished_game_stage(self, create_user):
        self.referee = create_user()
        self.player = create_user()
        self.referee_token, _ = Token.objects.get_or_create(user=self.referee)
        self.player_token, _  = Token.objects.get_or_create(user=self.player)
        self.map = Map(map_data='MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA A//\nENDMAP\nSTART 0 0 0', proposed_by=self.referee)
        self.map.save()
        self.stage = Stage(endpoint='test', running=True)
        self.stage.save()
        self.game = Game(map=self.map, stage=self.stage, player=self.player, finished=True, moves='ACC 1 1 1')
        self.game.save()

    @pytest.fixture
    def setup_finished_game_out_of_stage(self, create_user):
        self.referee = create_user()
        self.player = create_user()
        self.referee_token, _ = Token.objects.get_or_create(user=self.referee)
        self.player_token, _  = Token.objects.get_or_create(user=self.player)
        self.map = Map(map_data='MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA A//\nENDMAP\nSTART 0 0 0', proposed_by=self.referee)
        self.map.save()
        self.stage = Stage(endpoint='test', running=True)
        self.stage.save()
        self.game = Game(map=self.map, player=self.player, finished=True, moves='ACC 1 1 1')
        self.game.save()

    def test_score_game(self, api_client, setup_finished_game):
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + self.referee_token.key)
        response = api_client.get('/api/score/')
        assert response.status_code == 200, response.data
        assert response.data['game_id'] == self.game.id
        assert response.data['map_data'] == self.map.map_data
        assert response.data['moves'] == self.game.moves

        response = api_client.post('/api/score/', {'game_id': response.data['game_id'], 'score': 1})
        assert response.status_code == 200, response.data
        assert response.data['message'] == 'Score saved'

    def test_score_game_in_stage(self, api_client, setup_finished_game_stage):
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + self.referee_token.key)
        response = api_client.get(f'/api/score/{self.stage.endpoint}')
        assert response.status_code == 200, response.data
        assert response.data['game_id'] == self.game.id
        assert response.data['map_data'] == self.map.map_data
        assert response.data['moves'] == self.game.moves

        response = api_client.post('/api/score/', {'game_id': response.data['game_id'], 'score': 1})
        assert response.status_code == 200, response.data
        assert response.data['message'] == 'Score saved'

    def test_score_no_game_with_id(self, api_client, setup_finished_game):
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + self.referee_token.key)
        response = api_client.post('/api/score/', {'game_id': 999, 'score': 1})
        assert response.status_code == 404, response.data

    def test_score_inexistent_stage(self, api_client, setup_finished_game_stage):
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + self.referee_token.key)
        response = api_client.post('/api/score/phony_stage', {'game_id': self.game.id, 'score': 1})
        assert response.status_code == 404, response.data

    def test_score_game_in_different_stage(self, api_client, setup_finished_game_out_of_stage):
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + self.referee_token.key)
        response = api_client.post(f'/api/score/{self.stage.endpoint}', {'game_id': self.game.id, 'score': 1})
        assert response.status_code == 400, response.data

    def test_score_bad_referee(self, api_client, setup_finished_game):
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + self.player_token.key)
        response = api_client.post(f'/api/score/', {'game_id': self.game.id, 'score': 1})
        assert response.status_code == 403, response.data

    def test_score_already_scored(self, api_client, setup_finished_game):
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + self.referee_token.key)
        response = api_client.post('/api/score/', {'game_id': self.game.id, 'score': 1})
        assert response.status_code == 200, response.data
        assert response.data['message'] == 'Score saved'
        response = api_client.post('/api/score/', {'game_id': self.game.id, 'score': 1})
        assert response.status_code == 403, response.data
        assert response.data['message'] == 'This game has already been scored'

@pytest.mark.skip
class TestTeamScoreComputation:
    def test_simple_scores(self, create_user):
        user1 = create_user()
        team1 = Team(user=user1)
        team1.save()
        user2 = create_user()
        team2 = Team(user=user2)
        team2.save()

        stage1 = Stage(endpoint='test_scoring')
        stage1.save()

        map11 = Map(map_data='', proposed_by=user1)
        map11.save()
        map12 = Map(map_data='', proposed_by=user1)
        map12.save()
        map21 = Map(map_data='', proposed_by=user2)
        map21.save()
        map22 = Map(map_data='', proposed_by=user2)
        map22.save()

        stage1.maps.add(map11)
        stage1.maps.add(map12)
        stage1.maps.add(map21)
        stage1.maps.add(map22)

        g1_11 = Game(map=map11, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_12 = Game(map=map12, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_21 = Game(map=map21, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_22 = Game(map=map22, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_11.save()
        g1_12.save()
        g1_21.save()
        g1_22.save()


        g2_11 = Game(map=map11, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_12 = Game(map=map12, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_21 = Game(map=map21, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_22 = Game(map=map22, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_11.save()
        g2_12.save()
        g2_21.save()
        g2_22.save()

        Score(game=g1_11, referee=user1, score=3, valid=True).save()
        Score(game=g1_12, referee=user1, score=3, valid=True).save()
        Score(game=g2_11, referee=user1, score=4, valid=True).save()
        Score(game=g2_12, referee=user1, score=4, valid=True).save()

        Score(game=g1_21, referee=user2, score=3, valid=True).save()
        Score(game=g1_22, referee=user2, score=3, valid=True).save()
        Score(game=g2_21, referee=user2, score=4, valid=True).save()
        Score(game=g2_22, referee=user2, score=4, valid=True).save()

        assert team1.score_player == 0
        assert team2.score_player == 4
        assert team1.score_game == 4
        assert team2.score_game == 4

    def test_one_wrond_score(self, create_user):
        user1 = create_user()
        team1 = Team(user=user1)
        team1.save()

        stage1 = Stage(endpoint='test_scoring')
        stage1.save()

        map11 = Map(map_data='', proposed_by=user1)
        map11.save()
        map12 = Map(map_data='', proposed_by=user1)
        map12.save()

        stage1.maps.add(map11)
        stage1.maps.add(map12)

        g1_11 = Game(map=map11, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_12 = Game(map=map12, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_11.save()
        g1_12.save()

        Score(game=g1_11, referee=user1, score=3, valid=True).save()
        Score(game=g1_12, referee=user1, score=4, valid=True).save()


        assert team1.score_player == 0
        assert team1.score_game == 2+10

    def test_several_wrong_games_one_map(self, create_user):
        user1 = create_user()
        team1 = Team(user=user1)
        team1.save()
        user2 = create_user()
        team2 = Team(user=user2)
        team2.save()

        stage1 = Stage(endpoint='test_scoring')
        stage1.save()

        map11 = Map(map_data='', proposed_by=user1)
        map11.save()
        map12 = Map(map_data='', proposed_by=user1)
        map12.save()

        stage1.maps.add(map11)
        stage1.maps.add(map12)

        g1_11 = Game(map=map11, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_12 = Game(map=map12, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_11.save()
        g1_12.save()

        g2_11 = Game(map=map11, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_11.save()

        Score(game=g1_11, referee=user1, score=2, valid=True).save()
        Score(game=g1_12, referee=user1, score=3, valid=True).save()
        Score(game=g2_11, referee=user1, score=2, valid=True).save()

        assert team1.score_player == 0
        assert team2.score_player == 1
        assert team1.score_game == 3+10

    def test_non_resolvent(self, create_user):
        user1 = create_user()
        team1 = Team(user=user1)
        team1.save()
        user2 = create_user()
        team2 = Team(user=user2)
        team2.save()

        stage1 = Stage(endpoint='test_scoring')
        stage1.save()

        map11 = Map(map_data='', proposed_by=user1)
        map11.save()
        map12 = Map(map_data='', proposed_by=user1)
        map12.save()
        map21 = Map(map_data='', proposed_by=user2)
        map21.save()
        map22 = Map(map_data='', proposed_by=user2)
        map22.save()

        stage1.maps.add(map11)
        stage1.maps.add(map12)
        stage1.maps.add(map21)
        stage1.maps.add(map22)

        g1_11 = Game(map=map11, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_12 = Game(map=map12, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_21 = Game(map=map21, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_22 = Game(map=map22, player=user1, stage=stage1, victory=True, finished=True, reference_score=3)
        g1_11.save()
        g1_12.save()
        g1_21.save()
        g1_22.save()


        g2_11 = Game(map=map11, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_12 = Game(map=map12, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_21 = Game(map=map21, player=user2, stage=stage1, victory=True, finished=True, reference_score=4)
        g2_22 = Game(map=map22, player=user2, stage=stage1, victory=False, finished=True, reference_score=4)
        g2_11.save()
        g2_12.save()
        g2_21.save()
        g2_22.save()

        Score(game=g1_11, referee=user1, score=3, valid=True).save()
        Score(game=g1_12, referee=user1, score=3, valid=True).save()
        Score(game=g2_11, referee=user1, score=4, valid=True).save()
        Score(game=g2_12, referee=user1, score=4, valid=True).save()

        Score(game=g1_21, referee=user2, score=3, valid=True).save()
        Score(game=g1_22, referee=user2, score=3, valid=True).save()
        Score(game=g2_21, referee=user2, score=4, valid=True).save()
        Score(game=g2_22, referee=user2, score=4, valid=True).save()

        assert team1.score_player == 0
        assert team2.score_player == 3+5
        assert team1.score_game == 4
        assert team2.score_game == 3

@pytest.mark.only
class TestStageMechanics:

    def test_unfinished_games_upon_stage_end(self, create_user):
        user1 = create_user()
        user2 = create_user()

        m = Map(map_data='MAP 2 2 2\nAAA AAA\nAAA AAA\nAAA AAA\nAAA AAA\nENDMAP\nSTART 0 0 0', proposed_by=user1)
        m.save()

        s = Stage(endpoint='test', running=True)
        s.save()

        s.maps.add(m)

        g1 = Game(map=m, player=user1, stage=s, finished=False)
        g1.save()
        g2 = Game(map=m, player=user2, stage=s, finished=False)
        g2.save()

        s.running = False
        s.save()

        assert Game.objects.get(pk=g1.pk).finished
        assert Game.objects.get(pk=g2.pk).finished
        assert Game.objects.get(pk=g1.pk).victory == False
        assert Game.objects.get(pk=g2.pk).victory == False
