import json
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
import json
from collections import OrderedDict

from django.db import transaction

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
        model = UserProfileModel
        fields = ['kor_name', 'eng_name', 'gender', 'email', 'mobileno', 'pmobileno', 'email', 'register_date', 'birth_year']

class UserProfilePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileModel
        fields = ['mobileno', 'email']

class StudentProfilePutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileModel
        fields = ['mobileno', 'pmobileno', 'email']

class UserSerializer(serializers.ModelSerializer):
    user_category = UserCategorySerializer()

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email', 'user_category', 'userprofile']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_userprofile_serializer(self, user_category):
        if user_category.name == '학생':
            return StudentProfileSerializer()
        return UserProfileSerializer()

    def to_representation(self, instance):
        userprofile_serializer = self.get_userprofile_serializer(instance.user_category)
        self.fields['userprofile'] = userprofile_serializer
        return super().to_representation(instance)

    def update(self, instance, validated_data):
        userprofile_data = validated_data.pop('userprofile', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        if userprofile_data:
            user_profile_serializer = self.get_userprofile_serializer(instance.user_category)
            userprofile_instance = instance.userprofile
            for key, value in userprofile_data.items():
                setattr(userprofile_instance, key, value)
            userprofile_instance.save()
        
        instance.save()
        return instance

# class UserSiginUpSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserModel
#         fields = ["username", "password", "email", "user_category", "join_date", "userprofile"]

#         extra_kwargs = {
#             "username": {
#                 'error_messages': {
#                     'required': '아이디를 입력해주세요.',
#                     'invalid': '알맞은 형식의 아이디를 입력해주세요.'
#                 },
#             },
#             "email": {
#                 'error_messages': {
#                     'required': '이메일을 입력해주세요.',
#                     'invalid': '알맞은 형식의 이메일을 입력해주세요.'
#                 },
#             },
#         }
        
#     @transaction.atomic
#     def create(self, validated_data):
#         user_category_id = validated_data['user_category']
#         user_profile = validated_data.pop("userprofile", None)

#         user = UserModel.objects.create(
#             username=validated_data['username'],
#             email=validated_data['email'],
#             user_category=user_category_id,
#         )
#         user.set_password(validated_data['password'])
#         user.save()

#         if user_profile:
#             # user category가 학생인 경우 student profile 생성
#             if user_category_id.name == '학생':
#                 student_profile_serializer = StudentProfileSerializer(data=user_profile)
#                 student_profile_serializer.is_valid(raise_exception=True)
#                 student_profile_serializer.save(user=user)
#             else:
#                 # 학생이 아닌 경우 일반 profile 생성
#                 user_profile_serializer = UserProfileSerializer(data=user_profile)
#                 user_profile_serializer.is_valid(raise_exception=True)
#                 user_profile_serializer.save(user=user)

#         return user

class UserSiginUpSerializer(serializers.ModelSerializer):
    user_category = UserCategorySerializer()
    userprofile = UserProfileSerializer(write_only=True)

    class Meta:
        model = UserModel
        fields = ["username", "password", "email", "user_category", "join_date", "userprofile"]

        extra_kwargs = {
            "username": {
                'error_messages': {
                    'required': '아이디를 입력해주세요.',
                    'invalid': '알맞은 형식의 아이디를 입력해주세요.'
                },
            },
            "email": {
                'error_messages': {
                    'required': '이메일을 입력해주세요.',
                    'invalid': '알맞은 형식의 이메일을 입력해주세요.'
                },
            },
        }
        
    @transaction.atomic
    def create(self, validated_data):
        user_profile_data = validated_data.pop("userprofile", None)

        user = UserModel.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            user_category=validated_data['user_category'],
        )
        user.set_password(validated_data['password'])
        user.save()

        if user_profile_data:
            UserProfileModel.objects.create(
                user=user,
                **user_profile_data,
            )

        return user