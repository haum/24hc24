from django.urls import path

from .views import TokenTestView, NewMapView, NewGameView, ProposeSolutionView

urlpatterns = [
    path('tokentest', TokenTestView.as_view()),
    path('newmap', NewMapView.as_view()),
    path('game/new/<slug:stage_endpoint>', NewGameView.as_view()),
    path('game/new', NewGameView.as_view()),
    path('game/<int:game_id>/solve', ProposeSolutionView.as_view()),
]

