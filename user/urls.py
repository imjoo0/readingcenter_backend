# user/urls.py

from django.urls import path
from graphene_django.views import GraphQLView
from .schema import schema
from .views import get_csrf_token

urlpatterns = [
    path('get_csrf_token/', get_csrf_token),  # CSRF 토큰을 얻기 위한 URL
    path('graphql/', GraphQLView.as_view(graphiql=True, schema=schema)),  # GraphQLView를 등록합니다.
]
