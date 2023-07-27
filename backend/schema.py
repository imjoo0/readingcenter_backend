import jwt 
from datetime import datetime, timedelta
from django.conf import settings
import graphene
from graphene_django import DjangoObjectType
from graphene import Interface
from django.contrib.auth import get_user_model
from user.models import (
    User as UserModel,
    UserCategory as UserCategoryModel,
    Student as StudentProfileModel,
    Teacher as TeacherProfileModel,
    Manager as ManagerProfileModel
)
from academy.models import (
    Academy as AcademyModel,
    Lecture as LectureModel
)
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError

def create_jwt(user):
    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(hours=12)  # expires in 12 hours
    }
    refresh_payload = {
        "user_id": user.id,
        "username": user.username,
    }
    accessToken = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256").decode('utf-8')
    refreshToken = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256").decode('utf-8')
    return accessToken, refreshToken
  
# 데이터 처리
class AcademyType(DjangoObjectType):
    branchName = graphene.String()
    academyId = graphene.Int()  # Newly added
    
    class Meta:
        model = AcademyModel
        fields = ("id","branchName", "name", "location")

    def resolve_branchName(self, info):
        return self.branch.name
    
class StudentType(DjangoObjectType):
    class Meta:
        model = StudentProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_year', 'origin', 'pmobileno',)

    id = graphene.Int()
    academies = graphene.List(AcademyType)

    def resolve_id(self, info):
        return self.user.id

    def resolve_academies(self, info):
        if self.academies.exists():
            return self.academies.all()
        else:
            return []

class TeacherType(DjangoObjectType):
    class Meta:
        model = TeacherProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_year',)

    id = graphene.Int()
    academy = graphene.Field(AcademyType)
    
    def resolve_id(self, info):
        return self.user.id
    def resolve_academy(self, info):
        return self.academy

class ManagerType(DjangoObjectType):
    class Meta:
        model = ManagerProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_year',)

    id = graphene.Int()
    academies = graphene.List(AcademyType)
    
    def resolve_id(self, info):
        return self.user.id

    def resolve_academies(self, info):
        academies = AcademyModel.objects.filter(manager=self.user)
        if academies.exists():
            return academies
        else:
            return []

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ("id","username", "email", "userCategory", "is_staff")
    
    userCategory = graphene.String()
    studentProfile = graphene.Field(StudentType)
    teacherProfile = graphene.Field(TeacherType)
    managerProfile = graphene.Field(ManagerType)
    
    def resolve_userCategory(self, info):
        return self.user_category.name
    
    def resolve_studentProfile(self, info):
        return getattr(self, 'student', None)

    def resolve_teacherProfile(self, info):
        return getattr(self, 'teacher', None)

    def resolve_managerProfile(self, info):
        return getattr(self, 'manager', None)

class LectureType(DjangoObjectType):
    repeatDay = graphene.String()
    students = graphene.List(StudentType, description="강좌 수강 학생들")
    class Meta:
        model = LectureModel
        fields = ("id", "academy", "date","start_time", "end_time", "lecture_info", "teacher")
    
    def resolve_repeat_day(self, info):
        return self.get_repeat_day_display() 
    
    def resolve_students(self, info):
        return [student.student for student in self.students.all() if hasattr(student, 'student')]
    
    
# Mutation 
class CreateLecture(graphene.Mutation):
    class Arguments:
        academy_id = graphene.Int(required=True)
        date = graphene.Date(required=True)
        start_time = graphene.Time(required=True)
        end_time = graphene.Time(required=True)
        lecture_info = graphene.String(required=True)
        teacher_id = graphene.Int(required=True)
        repeat_day = graphene.Int(required=True)

    lecture = graphene.Field(LectureType)

    @staticmethod
    def mutate(root, info, academy_id, date, start_time, end_time, lecture_info, teacher_id, repeat_day):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to add a lecture.")
        
        academy = AcademyModel.objects.get(id=academy_id)
        teacher = UserModel.objects.get(id=teacher_id)

        lecture = LectureModel(
            academy=academy,
            date=date,
            repeat_day = repeat_day,
            start_time=start_time,
            end_time=end_time,
            lecture_info=lecture_info,
            teacher=teacher
        )
        lecture.save()

        return CreateLecture(lecture=lecture)

class DeleteLecture(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(root, info, id):
        try:
            LectureModel.objects.get(id=id).delete()
            success = True
        except LectureModel.DoesNotExist:
            success = False
        return DeleteLecture(success=success)

class AddStudentsToLecture(graphene.Mutation):
    class Arguments:
        lecture_id = graphene.Int(required=True)
        student_ids = graphene.List(graphene.Int, required=True)

    lecture = graphene.Field(LectureType)

    @staticmethod
    def mutate(root, info, lecture_id, student_ids):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to add students to a lecture.")

        lecture = LectureModel.objects.get(id=lecture_id)
        students = UserModel.objects.filter(id__in=student_ids)

        # Check if students are already added
        already_added_students = []
        for student in students:
            if student in lecture.students.all():
                already_added_students.append(student.id)

        # If any students are already added, raise an exception
        if already_added_students:
            raise Exception(f"Students with IDs {already_added_students} are already added to the lecture.")

        # Add students to the lecture
        lecture.students.add(*students)
        lecture.save()

        return AddStudentsToLecture(lecture=lecture)

class UpdateTeacherInLecture(graphene.Mutation):
    class Arguments:
        lecture_id = graphene.ID(required=True)
        new_teacher_id = graphene.ID(required=True)

    lecture = graphene.Field(LectureType)

    @staticmethod
    def mutate(root, info, lecture_id, new_teacher_id):
        try:
            # Find the objects
            lecture = LectureModel.objects.get(id=lecture_id)
            new_teacher = UserModel.objects.get(id=new_teacher_id)

            # Update the teacher
            lecture.teacher = new_teacher
            lecture.save()

            return UpdateTeacherInLecture(lecture=lecture)

        except LectureModel.DoesNotExist:
            raise Exception('Invalid Lecture ID!')
        
        except UserModel.DoesNotExist:
            raise Exception('Invalid User ID!')

class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=False)
        user_category = graphene.Int(required=True)

    user = graphene.Field(UserType)

    @staticmethod
    def mutate(root, info, username, password, user_category, email=None):
        user_category = UserCategoryModel.objects.get(id=user_category)
        user = UserModel.objects.create_user(username=username, password=password, user_category=user_category, email=email)
        return CreateUser(user=user)

class CreateStudentProfile(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        kor_name = graphene.String(required=True)
        eng_name = graphene.String(required=True)
        gender = graphene.String(required=True)
        mobileno = graphene.String(required=True)
        birth_year = graphene.Int(required=True)
        pmobileno = graphene.String(required=True)
        origin = graphene.String(required=True)

    student_profile = graphene.Field(StudentType)

    @staticmethod
    def mutate(root, info, user_id, kor_name, eng_name, gender, mobileno, birth_year, pmobileno, origin):
        user = UserModel.objects.get(id=user_id)
        student_profile = StudentProfileModel.objects.create(user=user, kor_name=kor_name, eng_name=eng_name, gender=gender, mobileno=mobileno, birth_year=birth_year, pmobileno=pmobileno, origin=origin)
        return CreateStudentProfile(student_profile=student_profile)

class CreateTeacherProfile(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        kor_name = graphene.String(required=True)
        eng_name = graphene.String(required=True)
        gender = graphene.String(required=True)
        mobileno = graphene.String(required=True)
        birth_year = graphene.Int(required=True)
        academy_id = graphene.Int(required=True)

    teacher_profile = graphene.Field(TeacherType)

    @staticmethod
    def mutate(root, info, user_id, kor_name, eng_name, gender, mobileno, birth_year, academy_id):
        user = UserModel.objects.get(id=user_id)
        academy = AcademyModel.objects.get(id=academy_id)
        teacher_profile = TeacherProfileModel.objects.create(user=user, kor_name=kor_name, eng_name=eng_name, gender=gender, mobileno=mobileno, birth_year=birth_year, academy=academy)
        return CreateTeacherProfile(teacher_profile=teacher_profile)

class CreateManagerProfile(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        kor_name = graphene.String(required=True)
        eng_name = graphene.String(required=True)
        gender = graphene.String(required=True)
        mobileno = graphene.String(required=True)
        birth_year = graphene.Int(required=True)

    manager_profile = graphene.Field(ManagerType)

    @staticmethod
    def mutate(root, info, user_id, kor_name, eng_name, gender, mobileno, birth_year):
        user = UserModel.objects.get(id=user_id)
        manager_profile = ManagerProfileModel.objects.create(user=user, kor_name=kor_name, eng_name=eng_name, gender=gender, mobileno=mobileno, birth_year=birth_year)
        return CreateManagerProfile(manager_profile=manager_profile)

class RefreshToken(graphene.Mutation):
    class Arguments:
        refreshToken = graphene.String(required=True)

    accessToken = graphene.String()
    refreshToken = graphene.String()

    def mutate(self, info, refreshToken):
        try:
            payload = jwt.decode(refreshToken, settings.SECRET_KEY, algorithms="HS256")
            user_id = payload.get('user_id')
            user = get_user_model().objects.get(id=user_id)
        except Exception as e:
            raise ValidationError("Invalid refresh token")

        access_payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(hours=12)  # expires in 12 hours
        }
        accessToken = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
        refreshToken = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        return RefreshToken(accessToken=accessToken, refreshToken=refreshToken) 

class UpdateStudentProfile(graphene.Mutation):
    class Arguments:
        kor_name = graphene.String(required=False)
        eng_name = graphene.String(required=False)

    student_profile = graphene.Field(StudentType)

    @staticmethod
    def mutate(root, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise ValidationError("You must be logged in to update a profile.")
        if user.user_category != 4:  # 4 is the category of Student
            raise ValidationError("You are not a student.")
        
        student_profile = StudentProfileModel.objects.get(user=user)
        for arg, value in kwargs.items():
            setattr(student_profile, arg, value)
        student_profile.save()
        
        return UpdateStudentProfile(student_profile=student_profile)

class UpdateManagerProfile(graphene.Mutation):
    class Arguments:
        mobileno = graphene.String(required=False)
        branch_id = graphene.String(required=False)
        academy_name = graphene.String(required=False)
        academy_location = graphene.String(required=False)

    manager_profile = graphene.Field(ManagerType)

    @staticmethod
    def mutate(root, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise ValidationError("You must be logged in to update a profile.")
        if user.user_category != 2:  # 2 is the category of Manager
            raise ValidationError("You are not a manager.")
        
        manager_profile = ManagerProfileModel.objects.get(user=user)
        for arg, value in kwargs.items():
            setattr(manager_profile, arg, value)
        manager_profile.save()
        
        return UpdateManagerProfile(manager_profile=manager_profile)

class UpdateTeacherProfile(graphene.Mutation):
    class Arguments:
        kor_name = graphene.String(required=False)
        eng_name = graphene.String(required=False)

    teacher_profile = graphene.Field(TeacherType)

    @staticmethod
    def mutate(root, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise ValidationError("You must be logged in to update a profile.")
        if user.user_category != 3:  # 3 is the category of Teacher
            raise ValidationError("You are not a teacher.")
        
        teacher_profile = TeacherProfileModel.objects.get(user=user)
        for arg, value in kwargs.items():
            setattr(teacher_profile, arg, value)
        teacher_profile.save()
        
        return UpdateTeacherProfile(teacher_profile=teacher_profile)
    
class RemoveStudentFromLecture(graphene.Mutation):
    class Arguments:
        lecture_id = graphene.ID(required=True)
        student_id = graphene.ID(required=True)

    lecture = graphene.Field(LectureType)

    @staticmethod
    def mutate(root, info, lecture_id, student_id):
        try:
            # Find the objects
            lecture = LectureModel.objects.get(id=lecture_id)
            student = UserModel.objects.get(id=student_id)

            # Remove the student from the lecture
            lecture.students.remove(student)
            lecture.save()

            return RemoveStudentFromLecture(lecture=lecture)

        except LectureModel.DoesNotExist:
            raise Exception('Invalid Lecture ID!')
        
        except UserModel.DoesNotExist:
            raise Exception('Invalid Student ID!')

class AddAcademyToUser(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        academy_id = graphene.Int(required=True)

    student_profile = graphene.Field(StudentType)
    manager_profile = graphene.Field(ManagerType)

    @staticmethod
    def mutate(root, info, user_id, academy_id):
        user = UserModel.objects.get(id=user_id)
        academy = AcademyModel.objects.get(id=academy_id)

        if user.user_category.id == 4:
            student_profile = StudentProfileModel.objects.get(user=user)
            student_profile.academies.add(academy)
            student_profile.save()
            return AddAcademyToUser(student_profile=student_profile)
        
        elif user.user_category.id == 3:
            teacher_profile = TeacherProfileModel.objects.get(user=user)
            teacher_profile.academy = academy
            teacher_profile.save()
            return AddAcademyToUser(teacher_profile=teacher_profile)
        
        elif user.user_category.id == 2:
            manager_profile = ManagerProfileModel.objects.get(user=user)
            manager_profile.academies.add(academy)
            manager_profile.save()
            return AddAcademyToUser(manager_profile=manager_profile)
        else:
            raise ValidationError("This mutation is only applicable to Student and Manager profiles.")

class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        user_category = graphene.String(required=True)
    user = graphene.Field(lambda: UserType)

    def mutate(self, info, username, email, password, user_category):
        student_category = UserCategoryModel.objects.get(name=user_category)
        user = UserModel.objects.create_user(username=username, email=email, password=password, user_category=student_category)

        return CreateUser(user=user)
    
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

        if user.user_category == 2 and not hasattr(user, 'manager'):
            ManagerProfileModel.objects.create(user=user)

        login(info.context, user)
        accessToken, refreshToken = create_jwt(user)

        return Login(accessToken=accessToken, refreshToken=refreshToken)

# 처리
class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    all_students = graphene.List(UserType) 
    user_details = graphene.Field(UserType, user_id=graphene.Int(required=True))
    academies = graphene.List(AcademyType)
    studentsInAcademy = graphene.List(StudentType, academyId=graphene.Int(required=True))
    all_lectures = graphene.List(LectureType)
    get_lectures_by_academy_and_date = graphene.List(LectureType, academy_id=graphene.Int(required=True), date=graphene.Date(required=True))

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    def resolve_all_students(self, info):
        users = get_user_model().objects.filter(user_category__id=4)
        print(users)
        return get_user_model().objects.filter(user_category__id=4)
    
    def resolve_user_details(self, info, user_id):
        return get_user_model().objects.get(id=user_id)
    
    def resolve_academies(self, info):  
        return AcademyModel.objects.all()

    def resolve_studentsInAcademy(self, info, academyId):
        return StudentProfileModel.objects.filter(academies__id=academyId)
    
    def resolve_all_lectures(self, info):
        return LectureModel.objects.all()
    
    def resolve_get_lectures_by_academy_and_date(root, info, academy_id, date):
        return LectureModel.objects.filter(academy_id=academy_id, date=date)

class Mutation(graphene.ObjectType):
    login = Login.Field()
    createUser = CreateUser.Field()
    refreshToken = RefreshToken.Field()
    updateStudentProfile = UpdateStudentProfile.Field()
    updateManagerProfile = UpdateManagerProfile.Field()
    updateTeacherProfile = UpdateTeacherProfile.Field()
    create_student_profile = CreateStudentProfile.Field()
    create_teacher_profile = CreateTeacherProfile.Field()
    create_manager_profile = CreateManagerProfile.Field()
    add_academy_to_user = AddAcademyToUser.Field()
    create_lecture = CreateLecture.Field()
    delete_lecture = DeleteLecture.Field()
    add_students_to_lecture = AddStudentsToLecture.Field()
    update_teacher_in_lecture = UpdateTeacherInLecture.Field()
    remove_student_from_lecture = RemoveStudentFromLecture.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
