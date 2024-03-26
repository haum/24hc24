from django.urls import path, include

from .views import TokenTestView, NewMapView, NewGameView, ProposeSolutionView, ScoreGameView

urlpatterns = [
    path('tokentest', TokenTestView.as_view()),
    path('map/new', NewMapView.as_view()),
    path('map/new/<slug:stage_endpoint>', NewMapView.as_view()),
    path('game/new/<slug:stage_endpoint>', NewGameView.as_view()),
    path('game/new', NewGameView.as_view()),
    path('game/<int:game_id>/solve', ProposeSolutionView.as_view()),
    path('score/', ScoreGameView.as_view()),
    path('score/<slug:stage_endpoint>', ScoreGameView.as_view()),
]

