from ast import literal_eval
from django.http import QueryDict
import json
from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate


from user.jwt_claim_serializer import FirstFarmTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework import permissions
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.jwt_claim_serializer import FirstFarmTokenObtainPairSerializer
from user.serializers import UserSerializer, UserSiginUpSerializer
from user.models import (
    User as UserModel,
    UserProfile as UserProfileModel,
    UserCategory as UserCategoryModel,
    Rank as UserRankModel
    )

# user/
class UserView(APIView):
    permission_classes = [permissions.AllowAny]       # 누구나 view 접근 가능

    # 사용자 정보 조회
    def get(self, request):
        user = request.user
        user_serializer = UserSerializer(user).data

        return Response(user_serializer, status=status.HTTP_200_OK)

    # 회원가입
    def post(self, request):
        data = request.data.copy()

        for i in data:
            if data[i] == "":
                return Response("회원정보가 없습니다.", status=status.HTTP_400_BAD_REQUEST)

        profile_data = data.pop('userprofile')[0]
        # img_data = data.pop('img')[0]

        profile_data = literal_eval(profile_data)

        # if img_data != "undefined":
        #     profile_data['img'] = img_data

        data['userprofile'] = profile_data

        serializer = UserSiginUpSerializer(data=data.dict(), context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 수정
    def put(self, request, obj_id):
        try:
            user = UserModel.objects.get(pk=obj_id)
        except user.DoesNotExist:
            return Response(status=404)

        data = request.data.copy()
        if data['img'] == 'undefined' or data['img'] is None:
            data['img'] = user.userprofile.img
        if data['location'] == '' or data['location'] is None:
            data['location'] = user.userprofile.location
        if data['introduction'] == '' or data['introduction'] is None:
            data['introduction'] = user.userprofile.introduction
        if data['prefer'] == '' or data['prefer'] is None:
            data['prefer'] = user.userprofile.prefer

        user.userprofile.location = data['location']
        user.userprofile.img = data['img']
        user.userprofile.introduction = data['introduction']
        user.userprofile.prefer = data['prefer']
        user.userprofile.save()
        return Response(status=status.HTTP_200_OK)


    # 회원탈퇴 = 삭제
    def delete(self, request, obj_id):
        if obj_id is None:
            return Response("invalid request", status=status.HTTP_400_BAD_REQUEST)
        else:
            user_id = obj_id
            user_object = UserModel.objects.get(id=user_id)
            user_object.delete()
            return Response("회원 탈퇴 완료", status=status.HTTP_200_OK)

# 로그아웃 user/api/logout
class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ReadingcenterTokenObtainPairSerializer(TokenObtainPairView):
    serializer_class = ReadingcenterTokenObtainPairSerializer