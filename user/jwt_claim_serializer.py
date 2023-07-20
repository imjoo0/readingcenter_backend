from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from user.models import UserCategory,UserProfile
from student.models import StudentProfile

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
            token['category'] = user.user_category.id
        else:
            token['category'] = None

        userprofile = UserProfile.objects.get(user=user)
        
        if isinstance(user.user_category, UserCategory) and user.user_category.name == '학생':
            try:
                userprofile = StudentProfile.objects.get(user=user)
            except StudentProfile.DoesNotExist:
                pass

        token['fullname'] = userprofile.kor_name + ' (' + userprofile.eng_name + ')'

        return token
