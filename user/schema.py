import graphene
import jwt 
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from graphene_django.types import DjangoObjectType
from user.models import (
    User as UserModel,
    UserCategory as UserCategoryModel,
    Student as StudentModel,
    Teacher as TeacherModel,
    Manager as ManagerModel,
)

def create_jwt(user):
    payload = {
        "user_id": user.id,
        "username": user.username,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

class UserType(DjangoObjectType):
    class Meta:
        model = UserModel

class UserCategoryType(DjangoObjectType):
    class Meta:
        model = UserCategoryModel

class Query(graphene.ObjectType):
    # 쿼리들을 여기에 추가합니다.
    pass

class LoginResult(graphene.ObjectType):
    accessToken = graphene.String()
    csrftoken = graphene.String()
    user = graphene.Field(UserType)
    academies = graphene.List(graphene.String)

class Mutation(graphene.ObjectType):
    # 로그인을 수행하는 mutation
    login = graphene.Field(LoginResult, username=graphene.String(required=True), password=graphene.String(required=True))
    
    # 로그인을 수행하는 mutation의 resolver 
    def resolve_login(self, info, username, password):
        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Invalid username or password")
        if user and user.is_active:
            if user.user_category.name == '선생님':
                try:
                    teacher = TeacherModel.objects.get(user=user)
                    if teacher.academy:
                        login(info.context, user)
                        payload = {"user_id": user.id, "username": user.username}
                        accessToken = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
                        return LoginResult(accessToken=accessToken, csrftoken=info.context.META.get('CSRF_COOKIE', ''), user=user, academies=teacher.academy.name)
                except TeacherModel.DoesNotExist:
                    pass
            elif user.user_category.name == '학생':
                try:
                    student = StudentModel.objects.get(user=user)
                    academies = student.academies.all()
                    login(info.context, user)
                    payload = {"user_id": user.id, "username": user.username}
                    accessToken = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
                    return LoginResult(accessToken=accessToken, csrftoken=info.context.META.get('CSRF_COOKIE', ''), user=user, academies=[academy.name for academy in academies])
                except StudentModel.DoesNotExist:
                    pass
        return None

schema = graphene.Schema(query=Query, mutation=Mutation)