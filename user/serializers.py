import json
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
import json
from collections import OrderedDict

from django.db import transaction

from student.models import StudentProfile as StudentProfileModel
from user.models import (
    User as UserModel,
    UserProfile as UserProfileModel,
    UserCategory as UserCategoryModel
)

class UserCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCategoryModel
        fields = ['id', 'name']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileModel
        fields = ['kor_name', 'eng_name', 'gender', 'mobileno', 'email', 'register_date', 'birth_year']

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfileModel
        fields = ['kor_name', 'eng_name', 'gender', 'email', 'mobileno', 'pmobileno', 'email', 'register_date', 'birth_year']

class UserProfilePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileModel
        fields = ['mobileno', 'email']

class StudentProfilePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfileModel
        fields = ['mobileno', 'pmobileno', 'email']

class UserSerializer(serializers.ModelSerializer):
    user_category = UserCategorySerializer()
    userprofile = UserProfileSerializer()

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email', 'user_category', 'userprofile']

        extra_kwargs = {
            # write_only : 해당 필드를 쓰기 전용으로 만들어 준다.
            # 쓰기 전용으로 설정 된 필드는 직렬화 된 데이터에서 보여지지 않는다.
            'password': {'write_only': True},  # default : False
        }
    def update(self, instance, validated_data):
        print(validated_data)
        print(instance.userprofile.items)
        for key,value in instance.userprofile.items():
            setattr(instance.userprofile,key,value)
        instance.userprofile.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()


        return instance

        # # 프로필 정보 수정
        # user_profile_object = instance.userprofile

        # for key, value in user_profile_object.items():
        #     setattr(user_profile_object, key, value)

        # user_profile_object.save()
        #
        # return instance


class UserSiginUpSerializer(serializers.ModelSerializer):
    userprofile = UserProfileSerializer(required=False)

    class Meta:
        model = UserModel
        fields = ["username", "password", "email", "user_category", "join_date", "userprofile"]

        extra_kwargs = {
            # write_only : 해당 필드를 쓰기 전용으로 만들어 준다.
            # 쓰기 전용으로 설정 된 필드는 직렬화 된 데이터에서 보여지지 않는다.
            "username": {
                # 유효성 검사
                'error_messages': {
                    # required : 값이 입력되지 않았을 때 보여지는 메세지
                    'required': '아이디를 입력해주세요.',
                    # invalid : 값의 포맷이 맞지 않을 때 보여지는 메세지
                    'invalid': '알맞은 형식의 아이디를 입력해주세요.'
                }, },
            "email": {
                # 유효성 검사
                # error_messages : 에러 메세지를 자유롭게 설정 할 수 있다.
                'error_messages': {
                    # required : 값이 입력되지 않았을 때 보여지는 메세지
                    'required': '이메일을 입력해주세요.',
                    # invalid : 값의 포맷이 맞지 않을 때 보여지는 메세지
                    'invalid': '알맞은 형식의 이메일을 입력해주세요.'
                },
            },
        }
        
    @transaction.atomic
    def create(self, validated_data):
        print("8번")
        print(validated_data)

        # User object 생성
        user_category_id = validated_data['user_category']
        user = UserModel.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            user_category=user_category_id,
        )
        user.set_password(validated_data['password'])

        # UserProfile object 생성
        user_profile = validated_data.pop("userprofile")
        if user_profile:
            # 첫 회원가입시 id = 1 : name = 씨앗 default
            UserProfileModel.objects.create(
                user=user,
                rank_id=1,
                **user_profile,
            )
            user.save()

        return user


class UserSiginPutSerializer(serializers.ModelSerializer):
    userprofile = UserProfilePutSerializer()

    class Meta:
        model = UserModel
        fields = ["username", "email", "userprofile"]

        extra_kwargs = {
            # write_only : 해당 필드를 쓰기 전용으로 만들어 준다.
            # 쓰기 전용으로 설정 된 필드는 직렬화 된 데이터에서 보여지지 않는다.
            "username": {
                'required': False,
            }
        }

    def update(self, instance, validated_data):
        print("6번")
        print(instance)
        print("7번")
        print(validated_data)

        user_profile = validated_data.pop("userprofile")
        print("8번")
        print(user_profile)

        # instance에는 입력된 object가 담긴다.
        # 유저 필수 정보 수정
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        # 프로필 정보 수정
        user_profile_object = instance.userprofile
        for key, value in user_profile.items():
            setattr(user_profile_object, key, value)

        user_profile_object.save()

        return instance
