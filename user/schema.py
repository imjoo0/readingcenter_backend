# your_app/schema.py
import graphene
from graphene_django.types import DjangoObjectType
from .models import User, UserProfile, UserCategory

class UserType(DjangoObjectType):
    class Meta:
        model = User

class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile

class UserCategoryType(DjangoObjectType):
    class Meta:
        model = UserCategory

class Query(graphene.ObjectType):
    # Define your queries here
    pass

class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        user_category_id = graphene.Int(required=True)

    user = graphene.Field(UserType)

    def mutate(self, info, username, password, email, user_category_id):
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            user_category_id=user_category_id
        )
        return CreateUser(user=user)

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()

class SignInMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    access_token = graphene.String()
    refresh_token = graphene.String()

    def mutate(self, info, username, password):
        # Perform your authentication logic here
        # You'll need to use a library like `django-graphql-jwt` or `graphene-django-extensions`
        # to handle user authentication and token generation
        # You can also perform other actions like creating user sessions, etc.

        # For example:
        # access_token, refresh_token = your_auth_function(username, password)

        return SignInMutation(access_token=access_token, refresh_token=refresh_token)

schema = graphene.Schema(query=Query, mutation=Mutation)
