import jwt 
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from django.conf import settings
import graphene
from graphene_file_upload.scalars import Upload
import pandas as pd
from graphene_django import DjangoObjectType
from graphene import Interface
from django.contrib.auth import get_user_model
from user.models import (
    User as UserModel,
    UserCategory as UserCategoryModel,
    Student as StudentProfileModel,
    Teacher as TeacherProfileModel,
    Manager as ManagerProfileModel,
    Remark as RemarkModel,
)
from academy.models import (
    Academy as AcademyModel,
    Lecture as LectureModel
)
from library.models import(
    Book as BookModel,
    BookInventory as BookInventoryModel,
    BookRental as BookRentalModel,
    BookReservation as BookReservationModel
)
from student.models import Attendance as AttendanceModel
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError, ObjectDoesNotExist

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
    
    class Meta:
        model = AcademyModel
        fields = ("id","branchName", "name", "location")

    def resolve_branchName(self, info):
        return self.branch.name

class AttendanceType(DjangoObjectType):
    class Meta:
        model = AttendanceModel
        fields = ("id","lecture", "student", "entry_time", "exit_time", "status")

    status_display = graphene.String()

    def resolve_status_display(self, info):
        return self.get_status_display()
    
class StudentType(DjangoObjectType):
    class Meta:
        model = StudentProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_date', 'origin', 'pmobileno','attendances')

    id = graphene.Int()
    academies = graphene.List(AcademyType)
    reserved_books_count = graphene.Int()
    lectures = graphene.List(lambda:LectureType)
    attendanceStatus =  graphene.List(lambda: AttendanceType, academyId = graphene.Int(), date = graphene.Date())
    
    def resolve_id(self, info):
        return self.user.id

    def resolve_academies(self, info):
        if self.academies.exists():
            return self.academies.all()
        else:
            return []
    
    def resolve_lectures(self, info):
        if self.lectures.exists():
            return self.lectures.all()
        else:
            return []
        
    def resolve_reserved_books_count(self, info):
        return len(BookReservationModel.objects.filter(student=self))
    
    def resolve_lecture_data(self,info,academyId,date):
        return LectureModel.objects.filter(academy_id = academyId, date = date, students__in = [self])
        
    def resolve_attendanceStatus(self,info,academyId,date):
        lectures = LectureModel.objects.filter(academy_id = academyId, date = date)
        return AttendanceModel.objects.filter(lecture__in=lectures, student=self)


    
class TeacherType(DjangoObjectType):
    class Meta:
        model = TeacherProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_date',)

    id = graphene.Int()
    academy = graphene.Field(AcademyType)
    
    def resolve_id(self, info):
        return self.user.id
    def resolve_academy(self, info):
        return self.academy

class ManagerType(DjangoObjectType):
    class Meta:
        model = ManagerProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_date',)

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

class Profile(graphene.Union):
    class Meta:
        types = (StudentType, TeacherType, ManagerType)
        
class BookInventoryType(DjangoObjectType):
    class Meta:
        model = BookInventoryModel
        fields = ("id","box_number","place","isbn","plbn","updatetime","reservations","book")
    
    booktitle = graphene.String()
    
    def resolve_booktitle(self, info):
        return self.book.title_ar
    
    def resolve_reservations(self,info):
        return self.reservations.id
    
class BookReservationType(DjangoObjectType):
    books = graphene.List(BookInventoryType)

    class Meta:
        model = BookReservationModel
        fields = ("id","lecture", "student", "books")

    def resolve_books(self, info):
        book_inventory_ids = self.books.values_list("id", flat=True)
        books = BookInventoryModel.objects.filter(id__in=book_inventory_ids)
        return books
        
class LectureType(DjangoObjectType):
    repeatDay = graphene.String()
    students = graphene.List(StudentType, description="강좌 수강 학생들")
    teacher = graphene.Field(TeacherType, description="강좌 담임 선생님")
    book_reservations = graphene.List(BookReservationType)
    attendanceStatus = graphene.Field(AttendanceType)

    class Meta:
        model = LectureModel
        fields = ("id", "academy", "date","start_time", "end_time", "lecture_info","attendances")
    
    def resolve_repeat_day(self, info):
        return self.get_repeat_day_display() 
    
    def resolve_students(self, info):
        return [student.student for student in self.students.all() if hasattr(student, 'student')]
    
    def resolve_teacher(self, info):
        if hasattr(self.teacher, 'teacher'):
            return self.teacher.teacher
        else:
            return None
            
    def resolve_book_reservations(self, info):
        return self.book_reservations.all()
    
    def resolve_attendanceStatus(self,info):
        try:
            AttendanceModel.objects.get(lecture=self, student__in=self.students)
        except AttendanceModel.DoesNotExist:
            return None
        
class StudentWithLectureType(graphene.ObjectType):
    student = graphene.Field(StudentType)
    lecture = graphene.Field(LectureType)
    attendanceStatus =  graphene.Field(AttendanceType)
    
    def __init__(self, student, lecture):
        self.student = student
        self.lecture = lecture
    
    # def resolve_lecture_data(self,info,academyId,date):
    #     return LectureModel.objects.get(academy_id = academyId, date = date, students__in = [self.student]).first()
    
    def resolve_attendanceStatus(self,info):
        try:
            return AttendanceModel.objects.get(lecture=self.lecture, student=self.student)
        except AttendanceModel.DoesNotExist:
            return None
    
class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ("id","username", "email", "userCategory", "is_staff","memos")
    
    userCategory = graphene.String()
    profile = graphene.Field(Profile)
    lectures = graphene.List(LectureType)
    
    def resolve_userCategory(self, info):
        if self.user_category is not None:
            return self.user_category.name
        return None
    
    def resolve_profile(self, info):
        if self.user_category.name == '학생':
            return getattr(self, 'student', None)
        elif self.user_category.name == '선생님':
            return getattr(self, 'teacher', None)
        elif self.user_category.name == '매니저':
            return getattr(self, 'manager', None)

class RemarkType(DjangoObjectType):
    class Meta:
        model = RemarkModel
        fields = ("id","memo", "user", "academy")

class BookType(DjangoObjectType):
    class Meta:
        model = BookModel
        fields = ("id","kplbn","title_ar","author_ar","title_lex","author_lex","fnf","il","litpro","lexile_code_ar","lexile_code_lex","ar_quiz","ar_pts","bl","wc_ar","wc_lex","lexile_ar","lexile_lex","books") 

    books = graphene.List(BookInventoryType)

    def resolve_books(self, info):
        return self.books.all()
        
# Mutation 
class CreateAttendance(graphene.Mutation):
    attendance = graphene.Field(AttendanceType)

    class Arguments:
        lecture_id = graphene.Int(required=True)
        student_id = graphene.Int(required=True)
        entry_time = graphene.DateTime(required=False)
        exit_time = graphene.DateTime(required=False)
        status_input = graphene.String(required=True)

    def mutate(self, info, lecture_id, student_id, status_input, entry_time=None, exit_time=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('로그인이 필요합니다')

        lecture = LectureModel.objects.get(id=lecture_id)
        student = StudentProfileModel.objects.get(user_id=student_id)

        if status_input not in ['attendance', 'completed', 'cancelled', 'late', 'absent', 'makeup']:
            raise Exception('등원 상태코드 값을 attendance, completed, cancelled, late, absent, makeup중 하나 선택해주세요 ')

        attendance = AttendanceModel.objects.filter(lecture=lecture, student=student).first()
        if not attendance:
            attendance = AttendanceModel(
                lecture=lecture,
                student=student
            )
        if status_input in ['attendance', 'late']:
            if not entry_time:
                raise Exception('등원시각을 입력해주세요')
            attendance.entry_time = entry_time
            attendance.exit_time = None
        elif status_input == 'completed':
            if not exit_time:
                raise Exception('하원 시간을 입력해주세요')
            if not attendance.entry_time:
                raise Exception(f'{student.kor_name}({student.eng_name}) 원생은 아직 출석하지 않았습니다')
            attendance.exit_time = exit_time
        else:
            attendance.entry_time = None
            attendance.exit_time = None

        attendance.status = status_input
        attendance.save()

class BookRegister(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    object = graphene.Field(BookType)  # Replace with your actual model type

    def mutate(self, info, file, **kwargs):
        try:
            df = pd.read_excel(file)
            for _, row in df.iterrows():
                model_instance = BookModel(
                    kplnbn=int(row[0]),
                    title_ar=row[1],
                    author_ar=row[2],
                    title_lex=row[3],
                    author_lex=row[4],
                    fnf=row[5],
                    il=row[6],
                    litpro=row[7],
                    lexile_code_ar=row[8],
                    lexile_code_lex=row[9],
                    ar_quiz=int(row[10]) if row[10] else None,
                    ar_pts=float(row[11]) if row[11] else None,
                    bl=float(row[12]) if row[12] else None,
                    wc_ar=int(row[13]) if row[13] else None,
                    wc_lex=int(row[14]) if row[14] else None,
                    lexile_ar=int(row[15]) if row[15] else None,
                    lexile_lex=int(row[16]) if row[16] else None
                    # Add more fields as needed
                )
                model_instance.save()
            return BookRegister(success=True, object=model_instance)
        except Exception as e:
            return BookRegister(success=False, errors=[str(e)])
        
class BookReservation(graphene.Mutation):
    class Arguments:
        student_id = graphene.ID(required=True)
        lecture_id = graphene.ID(required=True)
        book_inventory_ids = graphene.List(graphene.ID, required=True)

    book_reservation = graphene.Field(BookReservationType)

    @classmethod
    def mutate(cls, root, info, student_id, lecture_id, book_inventory_ids):
        # 학생, 강좌 및 책들을 가져옵니다.
        student = StudentProfileModel.objects.get(user__id=student_id)
        lecture = LectureModel.objects.get(id=lecture_id)
        books = BookInventoryModel.objects.filter(book_id__in=book_inventory_ids)
        if len(books) == 0:
            raise ValueError("해당하는 책이 존재하지 않습니다.")
        first_book = books[0]
        books = []
        books.append(first_book)
        # 예약을 생성합니다.
        book_reservation = BookReservationModel.objects.create(
            student=student,
            lecture=lecture
        )

        # 책들을 예약에 추가합니다.
        book_reservation.books.set(books)
        return BookReservation(book_reservation=book_reservation)
    
class DeleteBookReservations(graphene.Mutation):
    class Arguments:
        # 입력으로 도서 ID를 받음
        bookId = graphene.List(graphene.Int, required=True)

    # 결과로 삭제된 도서 ID를 반환
    deleted_book_ids = graphene.List(graphene.Int)

    def mutate(self, info, bookId):
        deleted_book_ids = []
        for book_id in bookId:
            # 해당 도서 ID와 일치하는 BookInventory 인스턴스를 가져옴
            book = BookInventoryModel.objects.get(id=book_id)
            
            # 해당 도서와 연결된 모든 BookReservation 인스턴스를 가져옴
            reservations = BookReservationModel.objects.filter(books__id=book_id)
            
            # 모든 연결된 BookReservation 인스턴스를 삭제
            for reservation in reservations:
                reservation.books.remove(book)
                # 만약 reservation이 더 이상 book을 가지고 있지 않다면, reservation 자체를 삭제
                if reservation.books.count() == 0:
                    reservation.delete()

            # 삭제된 도서 ID를 리스트에 추가
            deleted_book_ids.append(book_id)

        # 삭제된 도서 ID 리스트를 반환
        return DeleteBookReservations(deleted_book_ids=deleted_book_ids)

class DeleteLectureBookReservations(graphene.Mutation):
    class Arguments:
        # 입력으로 수업 ID를 받음
        lecture_id = graphene.ID(required=True)

    # 결과로 삭제된 도서 ID를 반환
    deleted_book_ids = graphene.List(graphene.Int)

    def mutate(self, info, lecture_id):
        deleted_book_ids = []
        # 해당 수업 ID와 일치하는 Lecture 인스턴스를 가져옴
        lecture = LectureModel.objects.get(id=lecture_id)

        # 해당 수업과 연결된 모든 BookReservation 인스턴스를 가져옴
        reservations = BookReservationModel.objects.filter(lecture=lecture)

        # 모든 연결된 BookReservation 인스턴스를 삭제
        for reservation in reservations:
            for book in reservation.books.all():
                # 삭제된 도서 ID를 리스트에 추가
                deleted_book_ids.append(book.id)
                # 도서를 예약에서 삭제
                reservation.books.remove(book)
                # 만약 reservation이 더 이상 book을 가지고 있지 않다면, reservation 자체를 삭제
                if reservation.books.count() == 0:
                    reservation.delete()
        
        # 삭제된 도서 ID 리스트를 반환
        return DeleteLectureBookReservations(deleted_book_ids=deleted_book_ids)

class DeleteStudentBookReservations(graphene.Mutation):
    class Arguments:
        # 입력으로 학생 ID를 받음
        student_id = graphene.ID(required=True)

    # 결과로 삭제된 도서 ID를 반환
    deleted_book_ids = graphene.List(graphene.Int)

    def mutate(self, info, student_id):
        deleted_book_ids = []
        # 해당 학생 ID와 일치하는 Student 인스턴스를 가져옴
        student = StudentProfileModel.objects.get(user__id=student_id)

        # 해당 학생과 연결된 모든 BookReservation 인스턴스를 가져옴
        reservations = BookReservationModel.objects.filter(student=student)

        # 모든 연결된 BookReservation 인스턴스를 삭제
        for reservation in reservations:
            for book in reservation.books.all():
                # 삭제된 도서 ID를 리스트에 추가
                deleted_book_ids.append(book.id)
                # 도서를 예약에서 삭제
                reservation.books.remove(book)
                # 만약 reservation이 더 이상 book을 가지고 있지 않다면, reservation 자체를 삭제
                if reservation.books.count() == 0:
                    reservation.delete()

        # 삭제된 도서 ID 리스트를 반환
        return DeleteStudentBookReservations(deleted_book_ids=deleted_book_ids)

class CreateLecture(graphene.Mutation):
    class Arguments:
        academy_id = graphene.Int(required=True)
        date = graphene.Date(required=True)
        start_time = graphene.Time(required=True)
        end_time = graphene.Time(required=True)
        lecture_info = graphene.String(required=True)
        teacher_id = graphene.Int(required=True)
        repeat_days = graphene.List(graphene.Int, required=True)
        repeat_weeks = graphene.Int(required=True)

    lecture_ids = graphene.List(graphene.Int)

    @staticmethod
    def mutate(root, info, academy_id, date, start_time, end_time, lecture_info, teacher_id, repeat_days,repeat_weeks):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to add a lecture.")
        
        academy = AcademyModel.objects.get(id=academy_id)
        teacher = TeacherProfileModel.objects.get(user_id=teacher_id)
        lecture_ids = []

        if -1 in repeat_days:
            lecture = LectureModel(
                academy=academy,
                date=date,
                repeat_day=-1,
                start_time=start_time,
                end_time=end_time,
                lecture_info=lecture_info,
                teacher=teacher
            )
            lecture.save()
            lecture_ids.append(lecture.id)
        else:
            start_date = date - timedelta(days=date.weekday())
            for week in range(repeat_weeks):
                for repeat_day in repeat_days:
                    next_date = start_date + timedelta(days=repeat_day)
                    lecture = LectureModel(
                        academy=academy,
                        date=next_date,
                        repeat_day=repeat_day,
                        start_time=start_time,
                        end_time=end_time,
                        lecture_info=lecture_info,
                        teacher=teacher
                    )
                    lecture.save()
                    lecture_ids.append(lecture.id)
                start_date += timedelta(days=7)

        return CreateLecture(lecture_ids=lecture_ids)

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
        students = StudentProfileModel.objects.filter(user_id__in=student_ids)

        # Check if students are already added
        already_added_students = []
        for student in students:
            if student in lecture.students.all():
                already_added_students.append(student.id)

        # If any students are already added, raise an exception
        if already_added_students:
            raise Exception(f"학생 id {already_added_students} 는 이미 해당강의에 수강신청했습니다")

        # Add students to the lecture
        lecture.students.add(*students)
        lecture.save()

        return AddStudentsToLecture(lecture=lecture)

class CreateMakeup(graphene.Mutation):
    class Arguments:
        lecture_id = graphene.Int(required=False)
        student_ids = graphene.List(graphene.Int, required=True)
        academy_id = graphene.Int(required=False)
        date = graphene.Date(required=False)
        start_time = graphene.Time(required=False)
        end_time = graphene.Time(required=False)
        lecture_info = graphene.String(required=False)
        teacher_id = graphene.Int(required=False)
        repeat_days = graphene.List(graphene.Int, required=False)
        repeat_weeks = graphene.Int(required=False)

    lecture_ids = graphene.List(graphene.Int)

    @staticmethod
    def mutate(root, info, student_ids, lecture_id=None, academy_id=None, date=None, start_time=None, end_time=None, lecture_info=None, teacher_id=None, repeat_days=None, repeat_weeks=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to add a lecture.")
        
        if lecture_id :
            lecture = LectureModel.objects.get(id=lecture_id)
        else:
            if not all([academy_id, date, start_time, end_time, lecture_info, teacher_id, repeat_days, repeat_weeks]):
                raise Exception("강의를 생성하기 위한 정보를 전부 입력해주세요")
            
            academy = AcademyModel.objects.get(id=academy_id)
            teacher = TeacherProfileModel.objects.get(user_id=teacher_id)
            lectures = []
            if -1 in repeat_days:
                lecture = LectureModel(
                    academy=academy,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    lecture_info=lecture_info,
                    teacher=teacher
                )
                lecture.save()
                lectures.append(lecture)
            else:
                start_date = date - timedelta(days=date.weekday())
                for week in range(repeat_weeks):
                    for repeat_day in repeat_days:
                        next_date = start_date + timedelta(days=repeat_day)
                        lecture = LectureModel(
                            academy=academy,
                            date=next_date,
                            start_time=start_time,
                            end_time=end_time,
                            lecture_info=lecture_info,
                            teacher=teacher
                        )
                        lecture.save()
                        lectures.append(lecture)
                    start_date += timedelta(days=7)

        students = StudentProfileModel.objects.filter(user_id__in=student_ids)
        for lecture in lectures:
            already_added_students = []
            for student in students:
                if student in lecture.students.all():
                    already_added_students.append(student.user_id)

            if already_added_students:
                raise Exception(f"학생 id {already_added_students} 는 이미 해당강의에 수강신청했습니다")

            lecture.students.add(*students)
            lecture.save()

        lecture_ids = [lecture.id for lecture in lectures]
        return CreateMakeup(lecture_ids=lecture_ids)    
        
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
        kor_name = graphene.String()
        eng_name = graphene.String()
        gender = graphene.String()
        mobileno = graphene.String()
        birth_date = graphene.Date()
        register_date = graphene.Date()
        pmobileno = graphene.String()
        origin = graphene.String()

    student_profile = graphene.Field(StudentType)

    @staticmethod
    def mutate(root, info, user_id, kor_name, eng_name, gender, mobileno, birth_date, register_date, pmobileno, origin):
        user = UserModel.objects.get(id=user_id)
        try:
            existing_student_profile = StudentProfileModel.objects.get(user=user)
            if kor_name:
                existing_student_profile.kor_name = kor_name
            if eng_name:
                existing_student_profile.eng_name = eng_name
            if gender:
                existing_student_profile.gender = gender
            if mobileno:
                existing_student_profile.mobileno = mobileno
            if birth_date:
                existing_student_profile.birth_date = birth_date
            if pmobileno:
                existing_student_profile.pmobileno = pmobileno
            existing_student_profile.save()
            return CreateStudentProfile(student_profile=existing_student_profile)
        except ObjectDoesNotExist:
            student_profile = StudentProfileModel.objects.create(
                user=user,
                kor_name=kor_name,
                eng_name=eng_name,
                gender=gender,
                mobileno=mobileno,
                birth_date=birth_date,
                register_date=register_date,
                pmobileno=pmobileno,
                origin=origin
            )
            return CreateStudentProfile(student_profile=student_profile)

class CreateTeacherProfile(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        kor_name = graphene.String(required=True)
        eng_name = graphene.String(required=True)
        gender = graphene.String(required=True)
        mobileno = graphene.String(required=True)
        birth_date = graphene.Date(required=True)
        academy_id = graphene.Int(required=True)

    teacher_profile = graphene.Field(TeacherType)

    @staticmethod
    def mutate(root, info, user_id, kor_name, eng_name, gender, mobileno, birth_date, academy_id):
        user = UserModel.objects.get(id=user_id)
        academy = AcademyModel.objects.get(id=academy_id)
        teacher_profile = TeacherProfileModel.objects.create(user=user, kor_name=kor_name, eng_name=eng_name, gender=gender, mobileno=mobileno, birth_date=birth_date, academy=academy)
        return CreateTeacherProfile(teacher_profile=teacher_profile)

class CreateManagerProfile(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        kor_name = graphene.String(required=True)
        eng_name = graphene.String(required=True)
        gender = graphene.String(required=True)
        mobileno = graphene.String(required=True)
        birth_date = graphene.Date(required=True)

    manager_profile = graphene.Field(ManagerType)

    @staticmethod
    def mutate(root, info, user_id, kor_name, eng_name, gender, mobileno, birth_date):
        user = UserModel.objects.get(id=user_id)
        manager_profile = ManagerProfileModel.objects.create(user=user, kor_name=kor_name, eng_name=eng_name, gender=gender, mobileno=mobileno, birth_date=birth_date)
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
        user_ids  = graphene.List(graphene.Int, required=True)
        academy_id = graphene.Int(required=True)

    student_profile = graphene.List(StudentType)  
    teacher_profile = graphene.List(TeacherType)
    manager_profile = graphene.List(ManagerType)

    @staticmethod
    def mutate(root, info, user_ids, academy_id):
        student_profiles = []
        teacher_profiles = []
        manager_profiles = []
        academy = AcademyModel.objects.get(id=academy_id)
        for user_id in user_ids:  # iterate over each user id
            user = UserModel.objects.get(id=user_id)

            if user.user_category.id == 4:
                student_profile = StudentProfileModel.objects.get(user=user)
                student_profile.academies.add(academy)
                student_profile.save()
                student_profiles.append(student_profile)

            elif user.user_category.id == 3:
                teacher_profile = TeacherProfileModel.objects.get(user=user)
                teacher_profile.academy = academy
                teacher_profile.save()
                teacher_profiles.append(teacher_profile)

            elif user.user_category.id == 2:
                manager_profile = ManagerProfileModel.objects.get(user=user)
                manager_profile.academies.add(academy)
                manager_profile.save()
                manager_profiles.append(manager_profile)
        return AddAcademyToUser(student_profile=student_profiles, teacher_profile=teacher_profiles, manager_profile=manager_profiles)

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
    
class CreateRemark(graphene.Mutation):
    class Arguments:
        memo = graphene.String(required=True)
        academyId = graphene.Int(required=True)
        userId = graphene.Int(required=True)

    remark = graphene.Field(RemarkType)

    def mutate(self, info, memo, academyId, userId):
        user = UserModel.objects.get(id = userId)
        if not user:
            raise ValidationError("해당 원생 정보를 찾을 수 없습니다")
        
        academy = AcademyModel.objects.get(id = academyId)
        if not academy:  
            raise ValidationError("해당 학원 정보를 찾을 수 없습니다")
        try:
            existing_remark = RemarkModel.objects.get(user=user, academy=academy)
            existing_remark.memo = memo
            existing_remark.save()
            return CreateRemark(remark=existing_remark)
        except RemarkModel.DoesNotExist:
            new_remark = RemarkModel.objects.create(memo=memo, user=user, academy=academy)
            new_remark.save()
            return CreateRemark(remark=new_remark)
 
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
    all_users = graphene.List(UserType) 
    user_details = graphene.Field(UserType, user_id=graphene.Int(required=True))
    academies = graphene.List(AcademyType)
    studentsInAcademy = graphene.List(StudentType, academyId=graphene.Int(required=True))
    all_lectures = graphene.List(LectureType, academyId=graphene.Int(required=True))
    get_lectures_book_count = graphene.List(BookReservationType, academy_id=graphene.Int(required=True))
    get_books_by_bl = graphene.List(
        BookType,
        minBl=graphene.Float(),
        maxBl=graphene.Float(),
        minWc=graphene.Int(),
        maxWc=graphene.Int(),
        academyId=graphene.Int(),
        lecture_date=graphene.Date(),
        plbn = graphene.Int()
    )
    get_books = graphene.List(BookType,academyId=graphene.Int())
    student_reserved_books = graphene.List(BookInventoryType, student_id=graphene.Int(required=True))
    get_attendance = graphene.List(StudentType, academyId=graphene.Int(required=True), date=graphene.Date(required=True), startTime=graphene.String(), endtime=graphene.String())
    get_lectures_by_academy_and_date_students = graphene.List(StudentWithLectureType, academy_id=graphene.Int(required=True), date=graphene.Date(required=True))

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    def resolve_all_students(self, info):
        return get_user_model().objects.filter(user_category__id=4)
    
    def resolve_all_users(self, info):
        return get_user_model().objects.all()
    
    def resolve_user_details(self, info, user_id):
        return get_user_model().objects.get(id=user_id)
    
    def resolve_academies(self, info):  
        return AcademyModel.objects.all()

    def resolve_studentsInAcademy(self, info, academyId):
        return StudentProfileModel.objects.filter(academies__id=academyId)
    
    def resolve_all_lectures(self, info, academyId):
        return LectureModel.objects.filter(academy_id=academyId)
    
    def resolve_get_lectures_by_academy_and_date_students(root, info, academy_id, date):
        lectures = LectureModel.objects.filter(academy_id=academy_id, date=date)
        # result = []
        # for lecture in lectures:
        #     result += lecture.students.all()
        # return result
        result = []
        for lecture in lectures:
            for student in lecture.students.all():
                swl = StudentWithLectureType(student=student, lecture=lecture)
                result.append(swl)
        return result
    
    def resolve_get_lectures_book_count(root, info, academy_id):
        lectures = LectureModel.objects.filter(academy_id=academy_id)
        reserved_books = BookReservationModel.objects.filter(lecture__in = lectures)
        return reserved_books
        
    def resolve_get_books_by_bl(self, info, minBl=None, maxBl=None, minWc=None, maxWc=None, academyId=None, lecture_date=None, plbn=None):
        if academyId is None:
            academyId = 2
        book_ids = BookInventoryModel.objects.filter(academy__id=academyId).values_list('book', flat=True)
        books = BookModel.objects.filter(id__in=book_ids)    
        if minBl is not None:
            books = books.filter(bl__gte=minBl)

        if maxBl is not None:
            books = books.filter(bl__lte=maxBl)

        if minWc is not None:
            books = books.filter(Q(wc_ar__gte=minWc) | Q(wc_lex__gte=minWc))

        if maxWc is not None:
            books = books.filter(Q(wc_ar__lte=maxWc) | Q(wc_lex__lte=maxWc))

        # Exclude books that are currently rented
        rented_book_ids = BookRentalModel.objects.filter(returned_at__isnull=True).values_list('book_inventory__book', flat=True)
        books = books.exclude(id__in=rented_book_ids)
        # Exclude books that are reserved for a lecture on the same date
        if lecture_date is not None:
            reserved_book_ids = BookReservationModel.objects.filter(lecture__date=lecture_date).values_list('books__id', flat=True)
            books = books.exclude(id__in=reserved_book_ids)
        return books
    
    def resolve_student_reserved_books(self, info, student_id):
        # `BookReservationModel`에서 해당 학생의 모든 예약을 조회합니다.
        student  = StudentProfileModel.objects.get(user__id=student_id)
        reservations  = BookReservationModel.objects.filter(student=student)
        books = []
        for reservation in reservations:
            books.extend(list(reservation.books.all()))
        return books
    
    def resolve_get_books(self, info, academyId=None):
        books = BookModel.objects.all()
        if academyId is not None:
            book_ids = BookInventoryModel.objects.filter(academy__id=academyId).values_list('book', flat=True)
            books = books.filter(id__in=book_ids)
        
        books = books.order_by('title_ar')
        return books
    
    def resolve_get_attendance(self, info, academyId, date, startTime, endtime):
        lectures = LectureModel.objects.filter(academy=academyId, date=date)
        # starttime과 endtime을 받아서 필터링합니다.
        if startTime:
            # 해당 시간과 일치하는 Lecture를 찾습니다.
            lectures = lectures.filter(start_time=startTime)

            # 해당 Lecture를 듣는 원생들 중에서 attendance가 아직 생성되지 않은 원생들을 찾습니다.
            students_attendance = AttendanceModel.objects.filter(lecture__in=lectures)
            students_without_attendance = lectures[0].students.exclude(user__id__in=students_attendance.values_list('student__user__id', flat=True))
            return students_without_attendance

        if endtime:
            # 해당 시간과 일치하는 Lecture를 찾습니다.
            lectures = lectures.filter(end_time=endtime)
            # 해당 Lecture를 듣는 원생들 중에서 attendance의 상태가 completed, makeup, absent가 아닌 원생들을 찾습니다.
            students_attendance = AttendanceModel.objects.filter(lecture__in=lectures).exclude(status__in=['completed', 'cancelled', 'absent','makeup'])
            target = None
            if(students_attendance):
                target = []
                for attendance in students_attendance:
                    target.append(attendance.student)
                return target

        # starttime과 endtime 모두 전달되지 않은 경우
        return None

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
    create_attendance = CreateAttendance.Field()
    reserve_books = BookReservation.Field()
    delete_book_reservations = DeleteBookReservations.Field()
    delete_lecture_book_reservations = DeleteLectureBookReservations.Field()
    delete_student_book_reservations = DeleteStudentBookReservations.Field()
    create_remark = CreateRemark.Field()
    create_makeup = CreateMakeup.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)