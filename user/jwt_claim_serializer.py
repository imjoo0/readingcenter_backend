from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from user.models import UserCategory,Student,Manager,Superuser,Teacher

class ReadingcenterTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # 생성된 토큰 가져오기
        token = super().get_token(user)

        # 사용자 지정 클레임 설정하기
        token['id'] = user.id
        token['username'] = user.username

        # user_category가 실제 UserCategory 모델의 인스턴스인지 확인
        if isinstance(user.user_category, UserCategory):
            token['category'] = user.user_category.name
        else:
            token['category'] = None

        if token['category'] == '학생':
            userprofile = Student.objects.get(user=user)
        elif token['category'] == '선생님':
            userprofile = Teacher.objects.get(user=user)
        elif token['category'] == '매니저':
            userprofile = Manager.objects.get(user=user)
        else:
            userprofile = Superuser.objects.get(user=user)

        token['fullname'] = userprofile.kor_name + ' (' + userprofile.eng_name + ')'

        return token
