from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ManifestationViewSet, ManifestationCategoryViewSet, WorkOrderViewSet, NearestPartnersView

app_name = 'reports'

# Router do DRF
router = DefaultRouter()
router.register(r'manifestations', ManifestationViewSet, basename='manifestation')
router.register(r'categories', ManifestationCategoryViewSet, basename='category')
router.register(r'work-orders', WorkOrderViewSet, basename='workorder')

urlpatterns = [
    path('nearest-partners/', NearestPartnersView.as_view(), name='nearest-partners'),
    path('', include(router.urls)),
]
