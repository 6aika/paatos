from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from decisions.api import (
    ActionViewSet, CaseViewSet, EventViewSet, FunctionViewSet,
    OrganizationViewSet, PostViewSet)

router = DefaultRouter()
router.register(r'action', ActionViewSet)
router.register(r'case', CaseViewSet)
router.register(r'function', FunctionViewSet)
router.register(r'event', EventViewSet)
router.register(r'organization', OrganizationViewSet)
router.register(r'post', PostViewSet)

urlpatterns = [
    url(r'^', include(router.urls, namespace='v1')),
]
