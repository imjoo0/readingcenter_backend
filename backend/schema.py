import graphene
import jwt
from user.models import User as UserModel
# 임의로 유저 정보를 가져오는 함수라고 가정합니다.
def get_user_by_username(username):
    return UserModel.objects.get(username=username)

class ObtainJSONWebToken(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    access_token = graphene.String()

    def mutate(self, info, username, password):
        # 유저 정보를 가져옵니다.
        user = get_user_by_username(username)

        # 유저 정보를 검증하는 로직 (예: 비밀번호 확인 등)을 추가할 수 있습니다.
        if not user.check_password(password):
            raise Exception("Invalid username or password")

        # 새로운 access_token을 생성합니다.
        access_token = jwt.encode({"user_id": user.id}, "secret_key", algorithm="HS256")

        # 생성된 토큰을 반환합니다.
        return ObtainJSONWebToken(access_token=access_token)

class Mutation(graphene.ObjectType):
    obtain_jwt_token = ObtainJSONWebToken.Field()

schema = graphene.Schema(mutation=Mutation)