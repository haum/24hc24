"""
URL configuration for server24hc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.views.generic import TemplateView
from django.urls import include, path
from django.conf.urls.static import static
from .settings import BASE_DIR

from serv.views import index, ListGamesView, ListMapsView, TeamView, show_game, show_map

urlpatterns = [
    path('poseidon/', admin.site.urls),
    path('', index, name='index'),
    path('viewer/', TemplateView.as_view(template_name='viewer.html'), name='viewer'),
    path('games', ListGamesView.as_view(), name='games_list'),
    path('team/<int:pk>', TeamView.as_view(template_name='team.html'), name='team'),
    path('game/<int:pk>', show_game, name='show_game'),
    path('maps', ListMapsView.as_view(), name='maps_list'),
    path('map/<int:pk>', show_map, name='show_map'),
    path('api/', include('serv.urls')),
] + static('/doc/', document_root=BASE_DIR / '..' / 'doc')
