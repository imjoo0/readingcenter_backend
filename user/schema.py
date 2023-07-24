import graphene
from graphene_django.types import DjangoObjectType
from .models import (User as UserModel,
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


class Mutation(graphene.ObjectType):
    # 로그인을 수행하는 mutation
    login = graphene.Field(UserType, id=graphene.String, password=graphene.String(), location=graphene.String())
    
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
