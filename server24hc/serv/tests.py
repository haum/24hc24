import uuid
import pytest
import random

from django.urls import reverse
from rest_framework.authtoken.models import Token
from .models import Map, Game, Stage

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
        response = api_client.post('/api/newmap', {'map': simple_map_str})
        assert response.status_code == 200
        db_map = Map.objects.all().last()
        assert db_map.map_data == simple_map_str
        assert db_map.proposed_by == token.user

    def test_new_map_no_arrival(self, api_client, get_or_create_token, invalid_map_str_no_arrival):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/newmap', {'map': invalid_map_str_no_arrival})
        assert response.status_code == 400
        assert response.data['message'] == 'Invalid map'
        assert response.data['map_error'] == 'No arrival'


    def test_add_map_to_running_stage(self, api_client, get_or_create_token, simple_map_str, stage_running):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/newmap', {'map': simple_map_str, 'stage': stage_running.endpoint})
        assert response.status_code == 200
        db_map = Map.objects.all().last()
        assert db_map.map_data == simple_map_str
        assert db_map.proposed_by == token.user
        assert stage_running.maps.count() == 1

    def test_add_map_to_non_running_stage(self, api_client, get_or_create_token, simple_map_str, stage):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/newmap', {'map': simple_map_str, 'stage': stage.endpoint})
        assert response.status_code == 403

    def test_add_map_to_non_exisitent_stage(self, api_client, get_or_create_token, simple_map_str):
        token = get_or_create_token
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post('/api/newmap', {'map': simple_map_str, 'stage': "phony"})
        assert response.status_code == 404

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
        self.game.delete()
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

    @pytest.mark.skip
    def test_valid_solution(self, api_client, setup_game_firstmap, first_map_solution):
        token = Token.objects.get(user=self.player_user)
        api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = api_client.post(f'/api/game/{self.game.id}/solve', {'moves': first_map_solution})
        assert response.status_code == 200, response.data
        assert response.data['victory']
        db_game = Game.objects.get(pk=self.game.id)
        assert db_game.finished
        assert db_game.moves == first_map_solution
        assert db_game.reference_score == 7.41666




# tests:
# - out of time
# - invalid move list
# - valid move list
# - game completion


