import jwt 
from datetime import datetime, timedelta
from django.conf import settings
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError

def create_jwt(user):
    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(hours=12)  # 12시간 후에 만료
    }
    refresh_payload = {
        "user_id": user.id,
        "username": user.username,
    }
    accessToken = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    refreshToken = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")
    return accessToken, refreshToken

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()

class RefreshToken(graphene.Mutation):
    class Arguments:
        refreshToken = graphene.String(required=True)

    accessToken = graphene.String()
    refreshToken = graphene.String()

    def mutate(self, info, refreshToken):
        # refreshToken을 이용해서 payload를 decode
        try:
            payload = jwt.decode(refreshToken, settings.SECRET_KEY, algorithms="HS256")
            user_id = payload.get('user_id')
            user = get_user_model().objects.get(id=user_id)
        except Exception as e:
            raise ValidationError("Invalid refresh token")

        # 새로운 accessToken을 생성해서 반환
        access_payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(hours=12)  # 12시간 후에 만료
        }
        accessToken = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
        refreshToken = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return RefreshToken(accessToken=accessToken, refreshToken=refreshToken) 
    
class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)
    accessToken = graphene.String()
    refreshToken = graphene.String()

    def mutate(self, info, username, password):
        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Invalid username or password")
        
        login(info.context, user)
        accessToken, refreshToken = create_jwt(user)  # JWT 토큰 생성 함수. 구현이 필요함.

        return Login(user=user, accessToken=accessToken, refreshToken=refreshToken)


class Query(graphene.ObjectType):
    user = graphene.Field(UserType, id=graphene.Int(required=True))  # 사용자 정보를 조회하기 위한 필드 정의

    def resolve_user(self, info, id):
        # 사용자 정보 조회 로직
        return get_user_model().objects.get(id=id)

class Mutation(graphene.ObjectType):
    login = Login.Field()
    refreshToken = RefreshToken.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
