from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TripViewSet, cities_list

router = DefaultRouter()
router.register(r'trips', TripViewSet, basename='trip')


urlpatterns = [
    path('', include(router.urls)),
    path('cities/', cities_list, name='cities-list'),
]
