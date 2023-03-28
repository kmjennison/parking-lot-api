
from django.urls import include, path
from rest_framework_nested import routers
from parking.apps.api import views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r'parking-lots', views.ParkingLotViewSet)

# Create a nested router to get spots by parking lot; ex: /api/parking-lot/2/spots/
parking_lots_router = routers.NestedSimpleRouter(router, r'parking-lots', lookup='parking_lot')
parking_lots_router.register(r'spots', views.SpotViewSet, basename='parking-lot-spots')
router.register(r'spots', views.SpotViewSet, basename='spot')
router.register(r'vehicles', views.VehicleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(parking_lots_router.urls)),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Login API for django-rest-framework browsable API.
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
