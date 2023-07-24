import graphene
from graphene_django.types import DjangoObjectType
from user.models import (User as UserModel,
                     UserCategory as UserCategoryModel,
                     Student as StudentModel,
                     Teacher as TeacherModel,
                     Manager as ManagerModel
                    )
from django.contrib.auth import authenticate

class UserType(DjangoObjectType):
    class Meta:
        model = UserModel

class UserCategoryType(DjangoObjectType):
    class Meta:
        model = UserCategoryModel

class Query(graphene.ObjectType):
    # 쿼리들을 여기에 추가합니다.
    pass

class Mutation(graphene.ObjectType):
    # 로그인을 수행하는 mutation
    login = graphene.Field(UserType, id=graphene.String(required=True), password=graphene.String(required=True), location=graphene.String(required=True))
    
    # 로그인을 수행하는 mutation의 resolver 
    def resolve_login(self, info, id, password, location):
        user = authenticate(username=id, password=password)
        if user and user.is_active:
            if user.user_category.name == '선생님':
                try:
                    teacher = TeacherModel.objects.get(user=user)
                    if teacher.academy.branch.name == location:
                        login(info.context, user)
                        return user
                except TeacherModel.DoesNotExist:
                    pass

            elif user.user_category.name == '학생':
                try:
                    student = StudentModel.objects.get(user=user)
                    academies = student.academies.all()
                    if any(academy.branch.name == location for academy in academies):
                        login(info.context, user)
                        return user
                except StudentModel.DoesNotExist:
                    pass
        return None
    
schema = graphene.Schema(query=Query, mutation=Mutation)
