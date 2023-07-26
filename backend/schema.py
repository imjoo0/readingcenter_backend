import jwt 
from datetime import datetime, timedelta
from django.conf import settings
import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from academy.models import Academy as AcademyModel
from user.models import (
    Student as StudentModel,
    Teacher as TeacherModel,
    Manager as ManagerModel,
    Superuser as SuperuserModel
)
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
    accessToken = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256").decode('utf-8')
    refreshToken = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256").decode('utf-8')
    return accessToken, refreshToken

class AcademyType(DjangoObjectType):
    branchName = graphene.String()
    
    class Meta:
        model = AcademyModel
        fields = ("branchName","name", "location")

    def resolve_branchName(self, info):
        return self.branch.name

class StudentType(DjangoObjectType):
    academies = graphene.List(AcademyType)
    korName = graphene.String(source='kor_name')
    engName = graphene.String(source='eng_name')
    gender = graphene.String()
    mobileno = graphene.String()
    registerDate = graphene.DateTime()
    
    class Meta:
        model = StudentModel
        fields = ('user', 'pmobileno', 'origin', 'korName','engName','gender','mobileno','registerDate','academies')

    def resolve_academies(self, info):
        return self.academies.all()

class TeacherType(DjangoObjectType):
    academy = graphene.Field(AcademyType)
    korName = graphene.String(source='kor_name')
    engName = graphene.String(source='eng_name')
    gender = graphene.String()
    mobileno = graphene.String()
    registerDate = graphene.DateTime()
    
    class Meta:
        model = TeacherModel
        fields = ('user', 'korName','engName','gender','mobileno','registerDate','academy' )

    def resolve_academy(self, info):
        return self.academy

class ManagerType(DjangoObjectType):
    academies = graphene.List(AcademyType)
    korName = graphene.String(source='kor_name')
    engName = graphene.String(source='eng_name')
    gender = graphene.String()
    mobileno = graphene.String()
    registerDate = graphene.DateTime()
    
    class Meta:
        model = ManagerModel
        fields = ('user', 'korName','engName','gender','mobileno','registerDate','academies' )

    def resolve_academies(self, info):
        return self.academies.all()

class SuperuserType(DjangoObjectType):
    academies = graphene.List(AcademyType)
    korName = graphene.String(source='kor_name')
    engName = graphene.String(source='eng_name')
    gender = graphene.String()
    mobileno = graphene.String()
    registerDate = graphene.DateTime()
    
    class Meta:
        model = SuperuserModel
        fields = ('user', 'korName','engName','gender','mobileno','registerDate','academies')

    def resolve_academies(self, info):
        return self.academies.all()

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ("username", "email")
    
    # 각 사용자 타입에 대한 별도의 필드를 추가
    userCategoryName = graphene.String() 
    studentProfile = graphene.Field(StudentType)
    teacherProfile = graphene.Field(TeacherType)
    managerProfile = graphene.Field(ManagerType)
    superuserProfile = graphene.Field(SuperuserType)

    # 각 사용자 타입에 대한 resolver를 추가
    def resolve_studentProfile(self, info):
        if self.user_category == 4 :
            return self.student
        return None

    def resolve_teacherProfile(self, info):
        if self.user_category == 3 :
            return self.teacher
        return None

    def resolve_managerProfile(self, info):
        if self.user_category == 2 :
            return self.manager
        return None

    def resolve_superuserProfile(self, info):
        if self.user_category == 1 :
            return self.superuser
        return None
    
    def resolve_userCategoryName(self, info):
        return self.user_category.name
    
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

    accessToken = graphene.String()
    refreshToken = graphene.String()

    def mutate(self, info, username, password):
        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Invalid username or password")
        
        # 사용자 카테고리가 '2'(Manager)인 경우에만 UserProfile을 생성합니다.
        if user.user_category == 2 and not hasattr(user, 'manager'):
            ManagerModel.objects.create(user=user)

        login(info.context, user)
        accessToken, refreshToken = create_jwt(user)

        return Login(accessToken=accessToken, refreshToken=refreshToken)


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)  # 로그인된 사용자 정보를 조회하기 위한 필드 정의
    academies = graphene.List(AcademyType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    def resolve_academies(self, info):  # 모든 아카데미를 반환하는 resolver
        return AcademyModel.objects.all()

class Mutation(graphene.ObjectType):
    login = Login.Field()
    refreshToken = RefreshToken.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
