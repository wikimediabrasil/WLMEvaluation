from django.urls import path
from . import views

app_name = "evaluations"
urlpatterns = [
    path("", views.home, name="home"),
    path("campaigns/new/", views.campaign_create, name="campaign_create"),
    path("campaigns/<int:campaign_id>/", views.vote, name="vote"),
    path("campaigns/<int:campaign_id>/p/<int:position>/", views.pair, name="pair"),
    path("campaigns/<int:campaign_id>/results/", views.results, name="results"),
]