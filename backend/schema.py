from django.db.models import Sum, Q, Avg, OuterRef, Subquery
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

import graphene
from graphene_file_upload.scalars import Upload
from graphene_django import DjangoObjectType
from graphene import InputObjectType
from graphene import Interface

import jwt 
import json
import pytz
import copy
import pandas as pd
from collections import defaultdict
from calendar import monthrange
from random import choice, sample
from dateutil.relativedelta import relativedelta

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
    LectureInfo as LectureInfoModel,
    Lecture as LectureModel
)
from library.models import(
    Book as BookModel,
    BookInventory as BookInventoryModel,
    BookRental as BookRentalModel,
    BookReservation as BookReservationModel,
    BookPkg as BookPkgModel
)
from student.models import(
    BookRecord as BookRecordModel,
    Attendance as AttendanceModel,
    SummaryReport as SummaryReportModel,
    MonthReport as MonthReportModel,
    RecommendFiction as RecommendFictionModel,
    RecommendNonFiction as RecommendNonFictionModel,
    Opinion as OpinionModel
) 

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
        fields = ("id","branchName", "name", "location","notification_interval", "end_notification_custom")

    def resolve_branchName(self, info):
        return self.branch.name

class AttendanceType(DjangoObjectType):
    class Meta:
        model = AttendanceModel
        fields = ("id","lecture", "student", "entry_time", "exit_time", "status", "memo")

    status_display = graphene.String()
    lecture_id = graphene.Int()

    def resolve_status_display(self, info):
        return self.get_status_display()

    def resolve_lecture_id(self, info):
        return self.lecture_id
    
class StudentType(DjangoObjectType):
    class Meta:
        model = StudentProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_date', 'origin', 'pmobileno','attendances')

    id = graphene.Int()
    academies = graphene.List(AcademyType)
    reserved_books_count = graphene.Int()
    lectures = graphene.List(lambda:LectureType, academyId=graphene.Int())
    
    def resolve_id(self, info):
        return self.user_id

    def resolve_academies(self, info):
        if self.academies.exists():
            return self.academies.all()
        else:
            return []
        
    def resolve_reserved_books_count(self, info):
        return len(BookReservationModel.objects.filter(student=self))
    
    # def resolve_lectures(self, info):
    #     return self.enrolled_lectures.all()

    def resolve_lectures(self, info, academyId=None):
        if academyId is not None:
            return self.enrolled_lectures.filter(academy_id=academyId)
        else:
            return self.enrolled_lectures.all()

class TeacherType(DjangoObjectType):
    class Meta:
        model = TeacherProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_date',)

    id = graphene.Int()
    academy = graphene.Field(AcademyType)
    
    def resolve_id(self, info):
        return self.user_id
    def resolve_academy(self, info):
        return self.academy

class ManagerType(DjangoObjectType):
    class Meta:
        model = ManagerProfileModel
        fields = ('user', 'kor_name', 'eng_name', 'gender', 'mobileno', 'register_date', 'birth_date',)

    id = graphene.Int()
    academies = graphene.List(AcademyType)
    
    def resolve_id(self, info):
        return self.user_id

    def resolve_academies(self, info):
        academies = self.academies.all()
        if academies:
            return academies
        else:
            return []

class Profile(graphene.Union):
    class Meta:
        types = (StudentType, TeacherType, ManagerType)
        
class BookInventoryType(DjangoObjectType):
    class Meta:
        model = BookInventoryModel
        fields = ("id","box_number","place","isbn","plbn","updatetime","status","reservations","book","rentals","academy")
    
    booktitle = graphene.String()
    book_status = graphene.String()
    is_available = graphene.Boolean() 
    inventory_num = graphene.Int()  
    reservations = graphene.List(lambda: BookReservationType)

    def resolve_book_status(self, info):
        return self.get_status_display()
    
    def resolve_booktitle(self, info):
        return self.book.title_ar
    
    def resolve_reservations(self,info):
        return self.reservations.all()
    
    # is_available 필드에 대한 resolver를 추가합니다.
    def resolve_is_available(self, info):
        return self.is_available 
    
    def resolve_inventory_num(self, info):
        return getattr(self, "temp_inventory_num", 0)
    
class BookReservationType(DjangoObjectType):
    books = graphene.List(BookInventoryType)

    class Meta:
        model = BookReservationModel
        fields = ("id","lecture", "student", "books")

    def resolve_books(self, info):
        book_inventory_ids = self.books.values_list("id", flat=True)
        books = BookInventoryModel.objects.filter(id__in=book_inventory_ids)
        return books

class BookRentalType(DjangoObjectType):
    class Meta:
        model = BookRentalModel
        fields = ("id","book_inventory", "student", "rented_at","due_date","returned_at","memo")
            
class LectureInfoType(DjangoObjectType):
    repeat_day = graphene.List(graphene.Int)
    class Meta:
        model = LectureInfoModel

    def resolve_repeat_day(self, info):
        repeat_days = self.repeat_day.get('repeat_days', [])
        return repeat_days
    
class LectureType(DjangoObjectType):
    students = graphene.List(StudentType, description="강좌 수강 학생들")
    teacher = graphene.Field(TeacherType, description="강좌 담임 선생님")
    lecture_info = graphene.Field(LectureInfoType, description="강좌 정보")
    book_reservations = graphene.List(BookReservationType)
    attendanceStatus = graphene.Field(AttendanceType, studentId=graphene.Int())

    class Meta:
        model = LectureModel
        fields = ("id", "academy", "date", "lecture_memo", "attendance", "teacher", "start_time", "end_time")
    
    def resolve_students(self, info):
        return self.students.all()
            
    def resolve_book_reservations(self, info):
        return self.book_reservation_list.all()
    
    def resolve_lecture_info(self, info):
        # 현재 강좌의 lecture_info 필드를 사용하여 강좌 정보를 가져옵니다.
        if self.lecture_info:
            return self.lecture_info
        else:
            return None
    
    def resolve_attendanceStatus(self,info, studentId=None):
        if studentId is not None:
            attendances = AttendanceModel.objects.filter(lecture=self,student__user_id = studentId)
        else:
            attendances = AttendanceModel.objects.filter(lecture=self)
        if attendances.exists():
            return attendances.first()  
        else:
            return None
            
class StudentWithLectureType(graphene.ObjectType):
    academy = graphene.Field(AcademyType)
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
        fields = ("id", "username", "email", "userCategory", "is_staff", "memos", "is_active")
    
    userCategory = graphene.String()
    profile = graphene.Field(Profile)
    
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

class OpinionType(DjangoObjectType):
    class Meta:
        model = OpinionModel

class BookRecordType(DjangoObjectType):
    class Meta:
        model = BookRecordModel
        fields = ("id","month","ar_date","lit_date","ar_correct","lit_correct","book","student") 

class BookType(DjangoObjectType):
    class Meta:
        model = BookModel
        fields = ("id","kplbn","title_ar","author_ar","title_lex","author_lex","lexile_code_ar","lexile_code_lex","ar_quiz","ar_pts","bl","wc_ar","wc_lex","lexile_ar","lexile_lex","books") 

    books = graphene.List(BookInventoryType, academyIds=graphene.List(graphene.ID))
    student_records = graphene.List(BookRecordType)

    
    il_status = graphene.String()
    fnf_status = graphene.String()
    litpro_status = graphene.String()

    def resolve_il_status(self, info):
        return self.get_il_display() if self.il else None

    def resolve_fnf_status(self, info):
        return self.get_fnf_display() if self.fnf else None
    
    def resolve_litpro_status(self, info):
        return self.get_litpro_display() if self.litpro is not None else None
    
    def resolve_books(self, info, academyIds=[]):
        if academyIds :
            return self.books.filter(academy__id__in=academyIds)
        return self.books.all()
    
    def resolve_student_records(self, info):
        # 현재 BookType의 인스턴스인 self를 이용하여 해당 도서를 읽은 학생들의 기록을 조회합니다.
        book_records = BookRecordModel.objects.filter(book=self)
        return book_records

class BookPkgType(DjangoObjectType):
    class Meta:
        model = BookPkgModel

class RecommendFictionType(DjangoObjectType):
    class Meta:
        model = RecommendFictionModel

class RecommendNonFictionType(DjangoObjectType):
    class Meta:
        model = RecommendNonFictionModel

class RecommendedBookUnion(graphene.Union):
    class Meta:
        types = (RecommendFictionType, RecommendNonFictionType)

class StudentBookRecordType(graphene.ObjectType):
    book_records = graphene.List(BookRecordType)
    book_pkg = graphene.Field(RecommendedBookUnion)

class DateStudentsType(graphene.ObjectType):
    date = graphene.Date(required=True)
    students = graphene.List(StudentWithLectureType, required=True)

class SummaryReportType(DjangoObjectType):
    class Meta:
        model = SummaryReportModel

class MonthReportType(DjangoObjectType):
    class Meta:
        model = MonthReportModel

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
        # else:
        #     attendance.entry_time = None
        #     attendance.exit_time = None

        attendance.status = status_input
        attendance.save()
        return CreateAttendance(attendance=attendance)

class CreateLectureMemo(graphene.Mutation):
    attendance = graphene.Field(AttendanceType)

    class Arguments:
        lecture_id = graphene.Int(required=True)
        student_id = graphene.Int(required=True)
        memo = graphene.String(required=True)

    def mutate(self, info, lecture_id, student_id, memo):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('로그인이 필요합니다')

        lecture = LectureModel.objects.get(id=lecture_id)
        student = StudentProfileModel.objects.get(user_id=student_id)

        attendance = AttendanceModel.objects.filter(lecture=lecture, student=student).first()
        if not attendance:
            # attendance = AttendanceModel(
            #     lecture=lecture,
            #     student=student
            # )
            raise Exception('출석 체크를 우선 해주세요')

        attendance.memo = memo
        attendance.save()
        return CreateLectureMemo(attendance=attendance)

# class BookRental(graphene.Mutation):
#     attendance = graphene.Field(AttendanceType)

#     class Arguments:
#         lecture_id = graphene.Int(required=True)
#         student_id = graphene.Int(required=True)
#         entry_time = graphene.DateTime(required=False)
#         exit_time = graphene.DateTime(required=False)
#         status_input = graphene.String(required=True)

#     def mutate(self, info, lecture_id, student_id, status_input, entry_time=None, exit_time=None):
#         user = info.context.user
#         if user.is_anonymous:
#             raise Exception('로그인이 필요합니다')

#         lecture = LectureModel.objects.get(id=lecture_id)
#         student = StudentProfileModel.objects.get(user_id=student_id)

#         if status_input not in ['attendance', 'completed', 'cancelled', 'late', 'absent', 'makeup']:
#             raise Exception('등원 상태코드 값을 attendance, completed, cancelled, late, absent, makeup중 하나 선택해주세요 ')

#         attendance = AttendanceModel.objects.filter(lecture=lecture, student=student).first()
#         if not attendance:
#             attendance = AttendanceModel(
#                 lecture=lecture,
#                 student=student
#             )
#         if status_input in ['attendance', 'late']:
#             if not entry_time:
#                 raise Exception('등원시각을 입력해주세요')
#             attendance.entry_time = entry_time
#             attendance.exit_time = None
#         elif status_input == 'completed':
#             if not exit_time:
#                 raise Exception('하원 시간을 입력해주세요')
#             if not attendance.entry_time:
#                 raise Exception(f'{student.kor_name}({student.eng_name}) 원생은 아직 출석하지 않았습니다')
#             attendance.exit_time = exit_time
#         # else:
#         #     attendance.entry_time = None
#         #     attendance.exit_time = None

#         attendance.status = status_input
#         attendance.save()

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
        
class BookInventoryUpdate(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        academyId = graphene.ID(required=False)
        newBoxNumber = graphene.String(required=False)
        bookStatus = graphene.Int(required=False)

    result = graphene.Field(BookInventoryType)

    @classmethod
    def mutate(cls, root, info, id, academyId, newBoxNumber, bookStatus):
        book_inven = BookInventoryModel.objects.get(id=id)
        if not book_inven :
            raise Exception("해당 도서가 재고에 없습니다")
        
        if academyId is not None:
            newAcademy = AcademyModel.objects.get(id = academyId)
            book_inven.academy = newAcademy
        
        if newBoxNumber is not None:
            book_inven.box_number = newBoxNumber

        if bookStatus is not None:
            book_inven.status = bookStatus

        book_inven.updatetime = timezone.now() 
        book_inven.save()
        return BookInventoryUpdate(result = book_inven)
    
class AddBookInventory(graphene.Mutation):
    class Arguments:
        bookId = graphene.ID(required=True)
        academyId = graphene.ID(required=True)
        boxNum = graphene.String(required=False)

    result = graphene.Field(BookInventoryType)

    @classmethod
    def mutate(cls, root, info, bookId, academyId, boxNum):
        target_book = BookModel.objects.get(id=bookId)
        newAcademy = AcademyModel.objects.get(id = academyId)

        if not target_book :
            raise Exception("해당 도서 정보가 없습니다. 본원으로 문의해주세요")
        
        if not newAcademy :
            raise Exception("아카데미 정보가 없습니다.")
        
        already_exists = BookInventoryModel.objects.filter(book__id=bookId,academy__id=academyId)
        
        # 각 plbn에서 9번째 이후의 값을 추출하고 정수로 변환
        entities = [int(exist.plbn[9:]) for exist in already_exists if exist.plbn and len(exist.plbn) > 9]

        if entities:
            max_entity = max(entities)
            book_inven = BookInventoryModel(
                plbn='PE'+str(target_book.kplbn)+str(max_entity + 1).zfill(4),
                book=target_book,
                box_number = boxNum,
                academy = newAcademy,
                status = 0
            )
            book_inven.save()
        else:
            book_inven = BookInventoryModel(
                plbn='PE'+str(target_book.kplbn)+str(1).zfill(4),
                book=target_book,
                box_number = boxNum,
                academy = newAcademy,
                status = 0
            )
            book_inven.save()
        return AddBookInventory(result = book_inven)

class DeleteBookInventory(graphene.Mutation):
    class Arguments:
        bookInvenId = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, bookInvenId):
        already_exist= BookInventoryModel.objects.filter(id=bookInvenId).first()
        
        if not already_exist:
            raise Exception("삭제하려는 도서 정보가 없습니다.")
        else:
            already_exist.delete()
            return DeleteBookInventory(success=True)
        
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
        book_inventory_ids = list(map(int, book_inventory_ids))
        # 예약을 생성합니다.
        book_reservation, is_created = BookReservationModel.objects.get_or_create(
            student=student,
            lecture=lecture
        )
        reservations = BookReservationModel.objects.filter(student=student)
        reserved_book_ids_list = []
        for reserv in reservations:
            reserved_books = reserv.books.all()
            if reserved_books:
                reserved_book_ids = list(reserved_books.values_list("id", flat=True))
                reserved_book_ids_list.extend(reserved_book_ids)

        # reserved_book_ids_list와 book_inventory_ids 배열 중에서 겹치지 않는 값을 추출
        not_reserved_book_ids = [bi for bi in book_inventory_ids if bi not in reserved_book_ids_list]
        not_reserved_books = BookInventoryModel.objects.filter(id__in=not_reserved_book_ids)
        if not_reserved_books:
            book_reservation.books.add(*not_reserved_books)
        else:
            raise Exception("이미 예약되어있는 도서입니다")
        return BookReservation(book_reservation=book_reservation)
    
class PlbnReservation(graphene.Mutation):
    class Arguments:
        student_id = graphene.ID(required=True)
        lecture_id = graphene.ID(required=True)
        plbn = graphene.String(required=True)

    book_reservation = graphene.Field(BookReservationType)

    @classmethod
    def mutate(cls, root, info, student_id, lecture_id, plbn):
        # 학생, 강좌 및 책들을 가져옵니다.
        student = StudentProfileModel.objects.get(user__id=student_id)
        lecture = LectureModel.objects.get(id=lecture_id)
        target_book = BookInventoryModel.objects.get(plbn = plbn)

        # 해당 도서가 이미 다른 학생에게 예약되어 있는지 확인
        existing_reservation = BookReservationModel.objects.filter(books=target_book).exclude(student=student).first()
        if existing_reservation:
            # 다른 학생의 예약을 삭제
            existing_reservation.books.remove(target_book)

        # 예약을 생성합니다.
        book_reservation, is_created = BookReservationModel.objects.get_or_create(
            student=student,
            lecture=lecture
        )
        
        reserved_books = book_reservation.books.all()
        if target_book not in reserved_books:
            book_reservation.books.add(target_book)
        else:
            raise Exception("이미 예약되어있는 도서입니다")

        return PlbnReservation(book_reservation=book_reservation)
   
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
    
# 두달치로 생성
def create_lectures_for_auto_add(academy, lecture_info, date, start_time, end_time, lecture_memo, teacher, repeat_days_dict, lecture_ids, new_students=None):
    # date 월의 마지막 날을 계산
    _, last_day_of_current_month = monthrange(date.year, date.month)
    end_date_of_current_month = date.replace(day=last_day_of_current_month)

    # date월 + 1월의 마지막 날을 계산
    _, last_day_of_next_month = monthrange(date.year, date.month + 1)
    end_date_of_next_month = (date + relativedelta(months=+1)).replace(day=last_day_of_next_month)

    # date부터 date월의 마지막 날까지 강의 생성
    current_date = date
    while current_date <= end_date_of_current_month:
        if current_date.weekday() in repeat_days_dict.get("repeat_days", []):
            create_and_save_lecture(academy, lecture_info, current_date, start_time, end_time, lecture_memo, teacher, lecture_ids, new_students)
        current_date += timedelta(days=1)

    # date월 + 1월의 첫 날부터 date월 + 1월의 마지막 날까지 강의 생성
    current_date = (date + relativedelta(months=+1)).replace(day=1)
    while current_date <= end_date_of_next_month:
        if current_date.weekday() in repeat_days_dict.get("repeat_days", []):
            create_and_save_lecture(academy, lecture_info, current_date, start_time, end_time, lecture_memo, teacher, lecture_ids, new_students)
        current_date += timedelta(days=1)


def create_and_save_lecture(academy, lecture_info, date, start_time, end_time, lecture_memo, teacher, lecture_ids, new_students=None):
    lecture = LectureModel(
        academy=academy,
        lecture_info=lecture_info,
        date=date,
        start_time=start_time,
        end_time=end_time,
        lecture_memo=lecture_memo,
        teacher=teacher,
    )
    lecture.save()
    if new_students:
        lecture.students.set(new_students)
    lecture_ids.append(lecture.id)
    return lecture

class CreateLecture(graphene.Mutation):
    class Arguments:
        # lectureInfo 
        repeat_days = graphene.String(required=True)
        repeat_weeks = graphene.Int(required=True)
        about = graphene.String(required=True)
        auto_add = graphene.Boolean(required=True)
        # lecture
        academy_id = graphene.Int(required=True) 
        date = graphene.Date(required=True) 
        start_time = graphene.Time(required=True)
        end_time = graphene.Time(required=True)
        lecture_memo = graphene.String(required=False)
        teacher_id = graphene.Int(required=True)
        student_ids = graphene.List(graphene.Int,required=True)

    lecture_ids = graphene.List(graphene.Int)

    @staticmethod
    def mutate(root, info, academy_id, date, start_time, end_time, about, teacher_id, repeat_days,repeat_weeks,auto_add, lecture_memo, student_ids):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to add a lecture.")
        
        try:
            academy = AcademyModel.objects.get(id=academy_id)
            teacher = TeacherProfileModel.objects.get(user_id=teacher_id)
        except (AcademyModel.DoesNotExist, TeacherProfileModel.DoesNotExist):
            raise Exception("Academy or Teacher not found.")
        
        # GraphQL에서 넘어온 문자열 형태의 JSON을 딕셔너리로 파싱
        try:
            repeat_days_dict = json.loads(repeat_days)
        except json.JSONDecodeError:
            raise Exception("Invalid JSON format for repeat_days.")

        lecture_ids = []

        lecture_info = LectureInfoModel(
            repeat_day=repeat_days_dict,
            about=about,
            auto_add = auto_add,
            repeat_weeks = repeat_weeks
        )

        lecture_info.save()
        new_students = StudentProfileModel.objects.filter(user_id__in=student_ids)
        if auto_add:
            create_lectures_for_auto_add(academy, lecture_info, date, start_time, end_time, lecture_memo, teacher, repeat_days_dict, lecture_ids, new_students)
        else:
            if -1 in repeat_days_dict.get("repeat_days", []):
                create_and_save_lecture(academy, lecture_info, date, start_time, end_time, lecture_memo, teacher, lecture_ids, new_students)
            else:
                # repeat_days에 있는 각 요일에 대해 수업 생성
                # 주의 해야 할 사항 : date 요일이 repeat_day와 동일한 경우 -> 주 단위가 한 주 빠르게 생성되게 된다. 
                # 예_ 수요일에 월화수 2주차 수업을 만든경우 수(만든 날짜) / 1주차 월화수 / 2주차 월화
                for repeat_day in repeat_days_dict.get("repeat_days", []):
                    for week in range(repeat_weeks): 
                        # 시작 날짜부터 해당 요일까지의 차이 계산
                        days_difference = (repeat_day - date.weekday() + 7) % 7
                        # 수업 날짜 설정
                        lecture_date = date + timedelta(days=days_difference) + timedelta(weeks=week)
                        create_and_save_lecture(academy, lecture_info, lecture_date, start_time, end_time, lecture_memo, teacher, lecture_ids, new_students)

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

        try:
            lecture = LectureModel.objects.get(id=lecture_id)
        except LectureModel.DoesNotExist:
            raise Exception("Invalid lecture ID")
        
        students = StudentProfileModel.objects.filter(user_id__in=student_ids)

        # 이미 추가된 학생인지 확인 
        already_added_students = [student.user_id for student in students if student in lecture.students.all()]
        if already_added_students:
            raise Exception(f"학생 id {already_added_students} 는 이미 해당강의에 수강신청했습니다")

        # Add students to the lecture
        lecture.students.add(*students)
        lecture.save()

        return AddStudentsToLecture(lecture=lecture)

class CreateMakeup(graphene.Mutation):
    class Arguments:
        lecture_id = graphene.Int(required=True)
        student_ids = graphene.List(graphene.Int, required=True)
        academy_id = graphene.Int()
        date = graphene.Date()
        start_time = graphene.Time()
        end_time = graphene.Time()
        teacher_id = graphene.Int()
        lecture_memo = graphene.String()
        about = graphene.String()

    lecture = graphene.Field(LectureType)

    @staticmethod
    def mutate(root, info, lecture_id, student_ids, academy_id=None, date=None, start_time=None, end_time=None, teacher_id=None, lecture_memo=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to create a makeup lecture.")

        try:
            lecture = LectureModel.objects.get(id=lecture_id)
        except LectureModel.DoesNotExist:
            raise Exception("Invalid lecture ID")

        # attendance 상태를 결석에서 보강으로 변경 합니다 . 
        attendance_records = AttendanceModel.objects.filter(lecture=lecture, student_id__in=student_ids)
        for record in attendance_records:
            record.status = 'makeup'
            record.save()
        lectures = []

        lecture_info = lecture.lecture_info
        academy = AcademyModel.objects.get(id=academy_id) if academy_id else lecture.academy
        teacher = TeacherProfileModel.objects.get(user_id=teacher_id) if teacher_id else lecture.teacher
        date = date if date else lecture.date
        start_time = start_time if start_time else lecture.start_time
        end_time = end_time if end_time else lecture.end_time
        lecture_memo = lecture_memo if lecture_memo else lecture.lecture_memo

        lecture = LectureModel(
            lecture_info=lecture_info,
            academy=academy,
            teacher=teacher,
            date=date,
            start_time=start_time,
            end_time=end_time,
            lecture_memo=lecture_memo,
        )
        lecture.save()
        lectures.append(lecture.id)
            
        # 원생 등록 
        students = StudentProfileModel.objects.filter(user_id__in=student_ids)
        lecture.students.add(*students)
        lecture.save()

        return CreateMakeup(lecture=lecture)

class UpdateLectureInfo(graphene.Mutation):
    class Arguments:
         # 필수 인자
        lecture_info_id = graphene.Int(required=True)
        date = graphene.Date(required=True) 
        about = graphene.String(required=True)
        repeat_days = graphene.String(required=True)
        repeat_weeks = graphene.Int(required=True)
        auto_add = graphene.Boolean(required=True)
        student_ids = graphene.List(graphene.Int, required=True)
        start_time = graphene.Time(required=True)
        end_time = graphene.Time(required=True)
        academy_id = graphene.Int(required=True)
        teacher_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, lecture_info_id, date, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to update a lecture info.")

        try:
            lecture_info =LectureInfoModel.objects.get(id=lecture_info_id)
        except LectureInfoModel.DoesNotExist:
            raise Exception("해당 강좌 정보가 존재하지 않습니다.")

        try:
            repeat_days_dict = json.loads(kwargs['repeat_days'])
        except json.JSONDecodeError:
            raise Exception("유효하지 않은 repeat_days 형식입니다.")
        
        try:
            old_lecture = LectureModel.objects.filter(lecture_info=lecture_info).latest('date')
        except LectureModel.DoesNotExist:
            raise Exception("기존 강좌 정보가 존재하지 않습니다.")
        
        old_repeat_days = lecture_info.repeat_day.get("repeat_days", [])
        new_repeat_days = repeat_days_dict.get("repeat_days", [])
        
        try:
            new_academy = AcademyModel.objects.get(id=kwargs.get('academy_id', old_lecture.academy.id))
            new_teacher = TeacherProfileModel.objects.get(user_id=kwargs.get('teacher_id', old_lecture.teacher.user_id))
            if 'student_ids' in kwargs:
                new_students = StudentProfileModel.objects.filter(user_id__in=kwargs['student_ids'])
            else:
                new_students = old_lecture.students.all()
        except (AcademyModel.DoesNotExist, TeacherProfileModel.DoesNotExist, StudentProfileModel.DoesNotExist) as e:
            raise Exception(str(e))
        
        # kwargs에서 필요한 값을 변수에 할당
        lecture_info.about = kwargs.get('about', lecture_info.about) 
        lecture_info.auto_add = kwargs.get('auto_add', lecture_info.auto_add)

        start_time = kwargs.get('start_time', old_lecture.start_time)
        end_time = kwargs.get('end_time', old_lecture.end_time)
        lecture_memo = kwargs.get('lecture_memo', old_lecture.lecture_memo)

        
        # 기존의 repeat_days를 변경하려는 경우
        lecture_info.repeat_day = repeat_days_dict
        # 기존에 만들었던 미래의 수업은 전부 삭제 
        LectureModel.objects.filter(lecture_info=lecture_info, date__gte=date).delete()
        # 반복 수업을 단일 수업으로 변경 
        if -1 in new_repeat_days:
            create_and_save_lecture(new_academy, lecture_info, date, start_time, end_time, lecture_memo, new_teacher, [], new_students)
        # 반복 수업 날짜 변경  
        else:
            lecture_info.repeat_weeks = kwargs.get('repeat_weeks', lecture_info.repeat_weeks) # 새로 입력 받은 값 혹은 기존 repeat_weeks로 진행 
            # auto_add True 이면 이달 말까지 생성
            if lecture_info.auto_add:
                create_lectures_for_auto_add(new_academy, lecture_info, date, start_time, end_time, lecture_memo, new_teacher, repeat_days_dict, [], new_students)
            else:
                for week in range(lecture_info.repeat_weeks):
                    for repeat_day in new_repeat_days:
                        # 시작 날짜부터 해당 요일까지의 차이 계산
                        # 수업 날짜 설정
                        next_date = date + timedelta(days=(int(repeat_day) - date.weekday() + 7) % 7) + timedelta(weeks=week)
                        create_and_save_lecture(new_academy, lecture_info, next_date, start_time, end_time, lecture_memo, new_teacher, [], new_students)                 
        lecture_info.save()
        return UpdateLectureInfo(success=True, message="해당 강좌의 정보가 전부 수정되었습니다.")
    
class UpdateLecture(graphene.Mutation):
    class Arguments:
         # 필수 인자
        lecture_id = graphene.Int(required=True)
        date = graphene.Date(required=True) 
        lecture_memo = graphene.String(required=False)
        student_ids = graphene.List(graphene.Int, required=True)
        start_time = graphene.Time(required=True)
        end_time = graphene.Time(required=True)
        academy_id = graphene.Int(required=True)
        teacher_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, lecture_id, date, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to update a lecture info.")

        try:
            lecture =LectureModel.objects.get(id=lecture_id)
        except LectureModel.DoesNotExist:
            raise Exception("기존 강좌 정보가 존재하지 않습니다.")
        
        try:
            if kwargs['academy_id'] != lecture.academy.id:
                lecture.academy = AcademyModel.objects.get(id=kwargs['academy_id'])
            if kwargs['teacher_id'] != lecture.teacher.user_id:
                lecture.teacher = TeacherProfileModel.objects.get(user_id=kwargs['teacher_id'])
            if 'student_ids' in kwargs:
                old_student_ids = set(lecture.students.values_list('user_id', flat=True))
                new_student_ids_set = set(kwargs['student_ids'])
                if old_student_ids != new_student_ids_set:
                    new_students = StudentProfileModel.objects.filter(user_id__in=kwargs['student_ids'])
                    lecture.students.set(new_students)
        except (AcademyModel.DoesNotExist, TeacherProfileModel.DoesNotExist, StudentProfileModel.DoesNotExist) as e:
            raise Exception(str(e))

        lecture.date = date
        lecture.lecture_memo = kwargs.get('lecture_memo', lecture.lecture_memo) 
        lecture.start_time = kwargs.get('start_time', lecture.start_time) 
        lecture.end_time = kwargs.get('end_time', lecture.end_time) 

        lecture.save()
        return UpdateLecture(success=True, message="해당 강좌의 정보가 수정되었습니다.")
    
class UpdateLectureStudents(graphene.Mutation):
    class Arguments:
         # 필수 인자
        lecture_id = graphene.Int(required=True)
        student_ids = graphene.List(graphene.Int, required=True)
        date = graphene.Date(required=True) 

        lecture_memo = graphene.String(required=False)
        start_time = graphene.Time(required=True)
        end_time = graphene.Time(required=True)
        academy_id = graphene.Int(required=True)
        teacher_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, lecture_id,student_ids, date, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Log in to update a lecture info.")

        # 1. lecture_id가 90인 Lecture 인스턴스를 가져옵니다.
        try:
            original_lecture = LectureModel.objects.get(id=lecture_id)
        except LectureModel.DoesNotExist:
            raise Exception("Lecture not found.")
        
        # 2. 그 인스턴스를 복사하여 새로운 Lecture 인스턴스를 생성합니다.
        new_lecture = copy.deepcopy(original_lecture)
        new_lecture.pk = None 
        new_lecture.save()
        
        try:
            if kwargs['academy_id'] != original_lecture.academy.id:
                new_lecture.academy = AcademyModel.objects.get(id=kwargs['academy_id'])
            if kwargs['teacher_id'] != original_lecture.teacher.user_id:
                new_lecture.teacher = TeacherProfileModel.objects.get(user_id=kwargs['teacher_id'])
        except (AcademyModel.DoesNotExist, TeacherProfileModel.DoesNotExist) as e:
            raise Exception(str(e))

        students = StudentProfileModel.objects.filter(user_id__in=student_ids)

        new_lecture.date = date
        new_lecture.lecture_memo = kwargs.get('lecture_memo', original_lecture.lecture_memo) 
        new_lecture.start_time = kwargs.get('start_time', original_lecture.start_time) 
        new_lecture.end_time = kwargs.get('end_time', original_lecture.end_time) 

        new_lecture.students.add(*students)
        original_lecture.students.remove(*students)
        new_lecture.save()
        return UpdateLecture(success=True, message="해당 강좌의 정보가 수정되었습니다.")
  
class DeleteLecture(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        
    success = graphene.Boolean()

    def mutate(root, info, id):
        try:
            lecture = LectureModel.objects.get(id=id)
            lecture.students.clear()
            lecture.delete()
            success = True
        except LectureModel.DoesNotExist:
            success = False
        return DeleteLecture(success=success)
    
# lectureinfo 와 연결된 모든 lecture와 학생 전부 삭제 
class DeleteLectureInfo(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        date = graphene.Date()

    success = graphene.Boolean()

    def mutate(root, info, id, date=None):
        try:
            mother_lecture = LectureInfoModel.objects.get(id=id)
            child_lectures = mother_lecture.lectureList.all()
            for child_lecture in child_lectures:
                if date and child_lecture.date < date:
                    continue
                child_lecture.students.clear()
                child_lecture.delete()

            # 모든 child_lecture가 삭제된 경우 mother_lecture도 삭제
            if not mother_lecture.lectureList.all().exists():
                mother_lecture.delete()
            success = True
        except LectureModel.DoesNotExist:
            success = False
        return DeleteLectureInfo(success=success)

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
            new_teacher = TeacherProfileModel.objects.get(user_id=new_teacher_id)

            # Update the teacher
            lecture.teacher = new_teacher
            lecture.save()

            return UpdateTeacherInLecture(lecture=lecture)

        except LectureModel.DoesNotExist:
            raise Exception('Invalid Lecture ID!')
        
        except UserModel.DoesNotExist:
            raise Exception('Invalid User ID!')

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
    
class UpdateAcademy(graphene.Mutation):
    class Arguments:
        academy_id = graphene.ID(required=True)
        notificationInterval = graphene.Int()
        endNotificationCustom = graphene.Boolean()

    academy = graphene.Field(AcademyType)

    @staticmethod
    def mutate(root, info, academy_id,notificationInterval=None,endNotificationCustom=None):
        academy = AcademyModel.objects.get(id=academy_id)
        if academy:
            if notificationInterval is not None:
                academy.notification_interval = notificationInterval
            if endNotificationCustom is not None:
                academy.end_notification_custom = endNotificationCustom
            academy.save()
            return UpdateAcademy(academy=academy)
        else:
            raise ValidationError("해당 아카데미 정보가 없습니다")

class UpdateUser(graphene.Mutation):
    class Arguments:
        user_id = graphene.ID(required=True)

    user = graphene.Field(UserType)

    @staticmethod
    def mutate(root, info, user_id):
        user = UserModel.objects.get(id=user_id)
        if user:
            user.is_active = not(user.is_active)
            user.save()
            return UpdateUser(user=user)
        else:
            raise ValidationError("해당 유저 정보가 없습니다")
    
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
    
# 단일 lecture에서 해당 원생 제외
class RemoveStudentFromLecture(graphene.Mutation):
    class Arguments:
        lecture_id = graphene.ID(required=True)
        student_ids = graphene.List(graphene.ID,required=True)

    lecture = graphene.Field(LectureType)

    @staticmethod
    def mutate(root, info, lecture_id, student_ids):
        try:
            # Find the objects
            lecture = LectureModel.objects.get(id=lecture_id)
            students = StudentProfileModel.objects.filter(user_id__in=student_ids)
            lecture.students.remove(*students)
            lecture.save()

            return RemoveStudentFromLecture(lecture=lecture)

        except LectureModel.DoesNotExist:
            raise Exception('Invalid Lecture ID!')
        
        except UserModel.DoesNotExist:
            raise Exception('Invalid Student ID!')

# 전체 lecture에서 해당 원생 제외 
class RemoveStudentFromLectureInfo(graphene.Mutation):
    class Arguments:
        lectureinfo_id = graphene.ID(required=True) # lectureInfo 의 id 
        student_ids = graphene.List(graphene.ID,required=True)

    lecture_info = graphene.Field(LectureInfoType)

    @staticmethod
    def mutate(root, info, lectureinfo_id, student_ids):
        try:
            # Find the objects
            lecture_info = LectureInfoModel.objects.get(id=lectureinfo_id)
            students = StudentProfileModel.objects.filter(user_id__in=student_ids)
            lectures = lecture_info.lectureList.all()
            for lecture in lectures:
                lecture.students.remove(*students)
                lecture.save()
            return RemoveStudentFromLecture(lecture_info=lecture_info)

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

class UpdateAcademyToUser(graphene.Mutation):
    class Arguments:
        user_id  = graphene.ID(required=True)
        academy_ids = graphene.List(graphene.Int,required=True)

    student_profile = graphene.Field(StudentType)  
    teacher_profile = graphene.Field(TeacherType)
    manager_profile = graphene.Field(ManagerType)

    @staticmethod
    def mutate(root, info, user_id, academy_ids):
        user = UserModel.objects.get(id=user_id)
        academies = AcademyModel.objects.filter(id__in=academy_ids)
        
        if user.user_category.id == 4:  # student일 경우 
            student_profile = StudentProfileModel.objects.get(user=user)
            student_profile.academies.set(academies)
            student_profile.save()
            return UpdateAcademyToUser(student_profile=student_profile)
        
        elif user.user_category.id == 5:  # teacher일 경우
            if len(academies) != 1:
                raise Exception("선생님의 ACADEMY는 하나여야 합니다. 매니저로 권한 요청하세요")
            teacher_profile = TeacherProfileModel.objects.get(user=user)
            teacher_profile.academy = academies.first()  # Set the single academy
            teacher_profile.save()
            return UpdateAcademyToUser(teacher_profile=teacher_profile)

        elif user.user_category.id == 6:  # manager 일 경우
            manager_profile = ManagerProfileModel.objects.get(user=user)
            manager_profile.academies.set(academies)
            manager_profile.save()
            return UpdateAcademyToUser(manager_profile=manager_profile)
        else:
            raise Exception("Invalid user category.")
        
class RemoveAcademyFromUser(graphene.Mutation):
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
                student_profile.academies.remove(academy)
                student_profile.save()
                student_profiles.append(student_profile)

            elif user.user_category.id == 3:
                teacher_profile = TeacherProfileModel.objects.get(user=user)
                teacher_profile.academy = None
                teacher_profile.save()
                teacher_profiles.append(teacher_profile)

            elif user.user_category.id == 2:
                manager_profile = ManagerProfileModel.objects.get(user=user)
                manager_profile.academies.remove(academy)
                manager_profile.save()
                manager_profiles.append(manager_profile)
        return RemoveAcademyFromUser(student_profile=student_profiles, teacher_profile=teacher_profiles, manager_profile=manager_profiles)
 
class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        user_category = graphene.String(required=True)
    user = graphene.Field(lambda: UserType)

    @staticmethod
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
 
class CreateOpinion(graphene.Mutation):
    class Arguments:
        contents = graphene.String(required=True)
        writer_id = graphene.ID(required=True)
        student_id = graphene.ID(required=True)
        date = graphene.Date(required=True)
        opinion_id = graphene.ID(required=False)

    opinion = graphene.Field(OpinionType)

    def mutate(self, info, contents, student_id, writer_id, date, opinion_id):
        user = UserModel.objects.get(id = writer_id)
        if not user:
            raise ValidationError("로그인을 해주세요")
        
        student = StudentProfileModel.objects.get(user__id = student_id)
        
        if not student:  
            raise ValidationError("해당 학생 정보를 찾을 수 없습니다")
        
        if opinion_id:
            old_opinion = OpinionModel.objects.get(id=opinion_id)
            old_opinion.contents = contents
            old_opinion.save()
            return CreateOpinion(opinion=old_opinion)
        
        new_opinion = OpinionModel.objects.create(contents=contents, writer=user, student=student, created_at = date)
        new_opinion.save()
        return CreateOpinion(opinion=new_opinion)

        
class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    accessToken = graphene.String()
    refreshToken = graphene.String()
    user_info = graphene.Field(UserType)

    def mutate(self, info, username, password):
        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Invalid username or password")

        if user.user_category == 2 and not hasattr(user, 'manager'):
            ManagerProfileModel.objects.create(user=user)

        login(info.context, user)
        accessToken, refreshToken = create_jwt(user)

        return Login(accessToken=accessToken, refreshToken=refreshToken,user_info = user)

class RecommendBookByRecord(graphene.Mutation):
    class Arguments:
        student_id = graphene.Int(required=True)
        academy_id = graphene.Int(required=True)
        book_record_ids = graphene.List(graphene.ID, required=True)
        f_nf = graphene.String(required=True)

    # 예약 가능한 추천 도서 목록을 반환:
    selected_books_inventory = graphene.List(BookInventoryType)

    @staticmethod
    def mutate(root, info, student_id, academy_id, f_nf,book_record_ids):
        records = BookRecordModel.objects.filter(id__in=book_record_ids)

        aggregates = records.aggregate(
            avg_ar_correct=Avg('ar_correct'),
            avg_bl=Avg('book__bl'),
            avg_wc_ar=Avg('book__wc_ar')
        )

        avg_ar_correct = aggregates['avg_ar_correct']
        avg_bl = aggregates['avg_bl']
        avg_wc_ar = aggregates['avg_wc_ar']

        model_to_use = RecommendFictionModel if f_nf == '1' else RecommendNonFictionModel
        already_recommended = model_to_use.objects.filter(student__user__id=student_id).values_list('pkg', flat=True)

        recommended_pkgs = BookPkgModel.objects.filter(
            fnf=f_nf,
            ar_min__lte=avg_bl,
            ar_max__gte=avg_bl,
            wc_min__lte=avg_wc_ar,
            wc_max__gte=avg_wc_ar,
            correct_min__lte=avg_ar_correct,
            correct_max__gte=avg_ar_correct
        ).exclude(name__in=already_recommended)

        if not recommended_pkgs.exists():
            try:
                latest_recommended = model_to_use.objects.filter(student__user__id=student_id).latest('created_at')
                recommended_pkgs = BookPkgModel.objects.filter(
                    fnf=f_nf,
                    ar_min__lte=avg_bl,
                    ar_max__gte=avg_bl,
                    wc_min__lte=avg_wc_ar,
                    wc_max__gte=avg_wc_ar,
                    correct_min__lte=avg_ar_correct,
                    correct_max__gte=avg_ar_correct
                ).exclude(name=latest_recommended.pkg)
            except model_to_use.DoesNotExist:
                pass

        # 학생이 읽은 도서의 목록을 가져옵니다.
        read_books = BookRecordModel.objects.filter(student__user__id=student_id).values_list('book', flat=True)

        while recommended_pkgs:
            selected_pkg = choice(recommended_pkgs)
            matching_books = selected_pkg.books.all() if selected_pkg.il == '0' else selected_pkg.books.filter(il=selected_pkg.il)
            # matching_books에서 학생이 읽은 도서들을 제외합니다.
            matching_books = matching_books.exclude(id__in=read_books)

            available_books_in_inventory = BookInventoryModel.objects.filter(book__in=matching_books, academy_id=academy_id)
            
            unavailable_inventory_items = set(BookReservationModel.objects.filter(books__in=available_books_in_inventory).values_list('books', flat=True))
            unavailable_inventory_items.update(BookRentalModel.objects.filter(book_inventory__in=available_books_in_inventory, returned_at__isnull=True).values_list('book_inventory', flat=True))
            # 예약되거나 렌탈된 도서의 인벤토리 항목을 제외
            available_inventory_items = [inventory_item for inventory_item in available_books_in_inventory if inventory_item.id not in unavailable_inventory_items]

            if available_inventory_items:
                count_to_sample = min(selected_pkg.il_count, len(available_inventory_items))
                selected_books_inventory = sample(list(available_inventory_items), count_to_sample)
                model_to_use.objects.create(
                    student=StudentProfileModel.objects.get(user_id=student_id),
                    pkg=selected_pkg.name
                )
                return RecommendBookByRecord(selected_books_inventory=selected_books_inventory)

            recommended_pkgs.remove(selected_pkg)

        raise Exception('변경할 도서패키지가 존재하지 않습니다')

class RecommendBookByPeriod(graphene.Mutation):
    class Arguments:
        student_id = graphene.Int(required=True)
        academy_id = graphene.Int(required=True)
        f_nf = graphene.String(required=True)

    # 예약 가능한 추천 도서 목록을 반환:
    selected_books_inventory = graphene.List(BookInventoryType)

    @staticmethod
    def mutate(root, info, student_id, academy_id, f_nf):
        model_to_use = RecommendFictionModel if f_nf == '1' else RecommendNonFictionModel

        # 최신 변경일 가져오기
        try:
            latest_change = model_to_use.objects.filter(student__user__id=student_id).latest('created_at').created_at
        except model_to_use.DoesNotExist:
            raise Exception('이전 패키지 변경일을 찾을 수 없습니다.')
        
        # 이전 패키지 변경일부터 현재까지의 리딩 기록 필터링
        records = BookRecordModel.objects.filter(student__user__id=student_id, ar_date__isnull=False, ar_date__range=(latest_change, timezone.now()+timedelta(hours=9)))

        # 만약 records가 빈 QuerySet이면 최근 6개월로 계산
        if not records:
            six_months_ago = timezone.now() - timedelta(days=180)
            records = BookRecordModel.objects.filter(student__user__id=student_id, ar_date__isnull=False, ar_date__range=(six_months_ago, timezone.now()+timedelta(hours=9)))
        
        aggregates = records.aggregate(
            avg_ar_correct=Avg('ar_correct'),
            avg_bl=Avg('book__bl'),
            avg_wc_ar=Avg('book__wc_ar')
        )

        avg_ar_correct = aggregates['avg_ar_correct']
        avg_bl = aggregates['avg_bl']
        avg_wc_ar = aggregates['avg_wc_ar']

        already_recommended = model_to_use.objects.filter(student__user__id=student_id).values_list('pkg', flat=True)

        recommended_pkgs = BookPkgModel.objects.filter(
            fnf=f_nf,
            ar_min__lte=avg_bl,
            ar_max__gte=avg_bl,
            wc_min__lte=avg_wc_ar,
            wc_max__gte=avg_wc_ar,
            correct_min__lte=avg_ar_correct,
            correct_max__gte=avg_ar_correct
        ).exclude(name__in=already_recommended)

        if not recommended_pkgs.exists():
            try:
                latest_recommended = model_to_use.objects.filter(student__user__id=student_id).latest('created_at')
                recommended_pkgs = BookPkgModel.objects.filter(
                    fnf=f_nf,
                    ar_min__lte=avg_bl,
                    ar_max__gte=avg_bl,
                    wc_min__lte=avg_wc_ar,
                    wc_max__gte=avg_wc_ar,
                    correct_min__lte=avg_ar_correct,
                    correct_max__gte=avg_ar_correct
                ).exclude(name=latest_recommended.pkg)
            except model_to_use.DoesNotExist:
                pass

        # 학생이 읽은 도서의 목록을 가져옵니다.
        read_books = BookRecordModel.objects.filter(student__user__id=student_id).values_list('book', flat=True)

        while recommended_pkgs:
            selected_pkg = choice(recommended_pkgs)
            matching_books = selected_pkg.books.all() if selected_pkg.il == '0' else selected_pkg.books.filter(il=selected_pkg.il)
            # matching_books에서 학생이 읽은 도서들을 제외합니다.
            matching_books = matching_books.exclude(id__in=read_books)

            available_books_in_inventory = BookInventoryModel.objects.filter(book__in=matching_books, academy_id=academy_id)
            
            unavailable_inventory_items = set(BookReservationModel.objects.filter(books__in=available_books_in_inventory).values_list('books', flat=True))
            unavailable_inventory_items.update(BookRentalModel.objects.filter(book_inventory__in=available_books_in_inventory, returned_at__isnull=True).values_list('book_inventory', flat=True))
            # 예약되거나 렌탈된 도서의 인벤토리 항목을 제외
            available_inventory_items = [inventory_item for inventory_item in available_books_in_inventory if inventory_item.id not in unavailable_inventory_items]

            if available_inventory_items:
                count_to_sample = min(selected_pkg.il_count, len(available_inventory_items))
                selected_books_inventory = sample(list(available_inventory_items), count_to_sample)
                model_to_use.objects.create(
                    student=StudentProfileModel.objects.get(user_id=student_id),
                    pkg=selected_pkg.name
                )
                return RecommendBookByRecord(selected_books_inventory=selected_books_inventory)

            recommended_pkgs.remove(selected_pkg)

        raise Exception('변경할 도서패키지가 존재하지 않습니다')

# 처리
class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    academy_info = graphene.Field(AcademyType, academy_id = graphene.ID(required=True))
    all_students = graphene.List(UserType) 
    all_users = graphene.List(UserType) 
    user_details = graphene.Field(UserType, user_id=graphene.Int(required=True), academy_id=graphene.Int(required=True))
    academies = graphene.List(AcademyType)
    studentsInAcademy = graphene.List(StudentType, academyId=graphene.Int(required=True))
    
    all_lectures = graphene.List(LectureType, academyId=graphene.Int(required=True))
    student_lectures = graphene.List(StudentWithLectureType, academyIds=graphene.List(graphene.ID,required=True), studentId = graphene.ID(required=True))

    get_lectures_book_count = graphene.List(BookReservationType, academy_id=graphene.Int(required=True))
    get_books_by_bl = graphene.List(
        BookType,
        studentId = graphene.ID(),
        minBl=graphene.Float(),
        maxBl=graphene.Float(),
        arQn=graphene.Int(),
        minWc=graphene.Int(),
        maxWc=graphene.Int(),
        minLex=graphene.Int(),
        maxLex=graphene.Int(),
        academyIds=graphene.List(graphene.ID,required=True),
        lecture_date=graphene.Date(),
        plbn = graphene.Int()
    )
    get_books = graphene.List(BookType,academyId=graphene.Int())
    student_reserved_books = graphene.List(BookInventoryType, student_id=graphene.Int(required=True))
    all_book_record = graphene.List(BookRecordType)
    
    student_book_record_with_pkg = graphene.Field(StudentBookRecordType, student_id=graphene.Int(required=True), f_nf=graphene.String(required=True))
    student_book_record = graphene.List(BookRecordType, student_id=graphene.Int(required=True))
    student_plbn_record = graphene.Field(graphene.Boolean, student_id=graphene.Int(required=True), plbn=graphene.String(required=True))

    get_attendance = graphene.List(StudentType, academyId=graphene.Int(required=True), date=graphene.Date(required=True), startTime=graphene.String(), endtime=graphene.String())
    get_student_lecture_history = graphene.List(AttendanceType, academyId=graphene.Int(required=True), studentId=graphene.Int(required=True))
    
    get_lecture_memo = graphene.List(AttendanceType,lectureId = graphene.ID(required=True))
    get_lecture_memo_by_student = graphene.List(AttendanceType,studentId = graphene.ID(required=True), academyIds=graphene.List(graphene.ID,required=True))

    get_customattendance = graphene.List(StudentType, academyId=graphene.Int(required=True), date=graphene.Date(required=True), entryTime=graphene.String(), endTime=graphene.String())
    
    get_lectures_by_academy_and_month = graphene.List(LectureType, academy_id=graphene.Int(required=True), month=graphene.Int(required=True))
    get_lecturestudents_by_academy_and_month = graphene.List(DateStudentsType, academy_id=graphene.Int(required=True), month=graphene.Int(required=True))

    get_lectures_by_academy_and_date = graphene.List(LectureType, academy_id=graphene.Int(required=True), date=graphene.Date(required=True))
    get_lectures_by_academy_and_date_students = graphene.List(StudentWithLectureType, academy_id=graphene.Int(required=True), date=graphene.Date(required=True))

    # 도서 대여 
    get_student_rental_status = graphene.List(BookRentalType,student_id=graphene.ID(required=False),book_id=graphene.ID(required=False))
    
    # 학습 리포트 
    get_summary_report = graphene.Field(SummaryReportType, student_id=graphene.Int(required=True), date=graphene.Date(required=True))
    get_month_reports = graphene.List(MonthReportType, student_id=graphene.Int(required=True), date=graphene.Date(required=True))
    get_opinion = graphene.List(OpinionType,student_id=graphene.ID(required=True), user_id=graphene.ID(required=True), date=graphene.Date(required=True))
    
    # 추천도서
    get_recommend_books = graphene.List(BookInventoryType, student_id=graphene.ID(required=True), academy_id=graphene.ID(required=True), f_nf=graphene.String(required=True), is_selected=graphene.Boolean(required=True))

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    def resolve_academy_info(self, info, academy_id):
        return AcademyModel.objects.get(id=academy_id)
    
    def resolve_all_students(self, info):
        return get_user_model().objects.filter(user_category__id=4)
    
    def resolve_all_users(self, info):
        return get_user_model().objects.all()
    
    def resolve_user_details(self, info, user_id , academy_id):
        return get_user_model().objects.get(id=user_id)
    
    def resolve_academies(self, info):  
        return AcademyModel.objects.all()

    def resolve_studentsInAcademy(self, info, academyId):
        return StudentProfileModel.objects.filter(academies__id=academyId)
    
    def resolve_all_lectures(self, info, academyId):
        return LectureModel.objects.filter(academy_id=academyId)
    
    def resolve_student_lectures(self, info, academyIds, studentId):
        student  = StudentProfileModel.objects.get(user__id=studentId)
        academies = AcademyModel.objects.filter(id__in=academyIds)
        student_lectures = LectureModel.objects.filter(students=student, academy__in=academies)
        result = []
        for lecture in student_lectures:
            swl = StudentWithLectureType(student=student, lecture=lecture)
            result.append(swl)
        return result
    
    def resolve_get_lectures_by_academy_and_month(root, info, academy_id, month):
        current_year = datetime.now().year
        lectures = LectureModel.objects.filter(academy_id=academy_id, date__month=month, date__year=current_year)
        return lectures
    
    def resolve_get_lecturestudents_by_academy_and_month(root, info, academy_id, month):
        current_year = datetime.now().year
        lectures = LectureModel.objects.filter(academy_id=academy_id, date__month=month, date__year=current_year)

        # 각 날짜별 학생들을 저장할 딕셔너리
        students_by_date = defaultdict(list)

        for lecture in lectures:
            date = lecture.date
            students = lecture.students.all()
            for student in students:
                # 중복 학생을 방지하기 위해 학생이 해당 날짜의 리스트에 없으면 추가
                if student not in students_by_date[date]:
                    swl = StudentWithLectureType(student=student, lecture=lecture)
                    students_by_date[date].append(swl)

        # 결과를 DateStudentsType 형태로 변환
        result = []
        for date, swl in students_by_date.items():
            result.append(DateStudentsType(date=date, students=swl))

        return result
       
    def resolve_get_lectures_by_academy_and_date(root, info, academy_id, date):
        lectures = LectureModel.objects.filter(academy_id=academy_id, date=date)
        for lecture in lectures:
            for student in lecture.students.all():
                student.lecture_id = lecture.id
        return lectures
    
    def resolve_get_lectures_by_academy_and_date_students(root, info, academy_id, date):
        lectures = LectureModel.objects.filter(academy_id=academy_id, date=date)
        result = []
        for lecture in lectures:
            for student in lecture.students.all():
                swl = StudentWithLectureType(student=student, lecture=lecture)
                result.append(swl)

        # day_of_week = date.weekday() # 0 월요일 / 1 화요일 .. 6 일요일 
        # auto_addLectures = LectureModel.objects.filter(
            # Q(academy_id=academy_id) & Q(auto_add=True) & Q(repeat_day=day_of_week) & ~Q(date__gte=date)
        # )
        # for lecture in auto_addLectures:
        #     new_lecture = LectureModel(
        #         academy_id=lecture.academy_id,
        #         date=date,
        #         repeat_day=lecture.repeat_day,
        #         start_time=lecture.start_time,
        #         end_time=lecture.end_time,
        #         lecture_info=lecture.lecture_info,
        #         teacher=lecture.teacher,
        #         auto_add = True 
        #     )
        #     new_students = lecture.students.all()
        #     new_lecture.save()
        #     new_lecture.students.add(*new_students)
        #     new_lecture.save()
        #     lecture.auto_add = False
        #     lecture.save()

        #     for student in new_students:
        #         swl = StudentWithLectureType(student=student, lecture=new_lecture)
        #         result.append(swl)
        return result
    
    def resolve_get_lectures_book_count(root, info, academy_id):
        lectures = LectureModel.objects.filter(academy_id=academy_id)
        reserved_books = BookReservationModel.objects.filter(lecture__in = lectures)
        return reserved_books
        
    def resolve_get_books_by_bl(self, info, studentId=None, minBl=None, maxBl=None, minWc=None, maxWc=None, minLex=None, maxLex=None, academyIds=[], lecture_date=None, arQn=None):
        if not academyIds:
            raise Exception('아카데미 id 값이 누락되었습니다.')
        
        # book_ids = BookInventoryModel.objects.filter(academy__id__in=academyIds).values_list('book', flat=True)
        # print(book_ids[0])
        # books = BookModel.objects.filter(id__in=book_ids) 

        books = BookModel.objects.filter(books__academy_id__in=academyIds).distinct()
        
        if arQn is not None:
            target = books.filter(ar_quiz=arQn)
            return target

        if studentId is not None:
            student_read_book_ids = BookRecordModel.objects.filter(student_id=studentId).values_list('book', flat=True)
            books = books.exclude(id__in=student_read_book_ids)
        
        if minBl is not None:
            books = books.filter(bl__gte=minBl)

        if maxBl is not None:
            books = books.filter(bl__lte=maxBl)

        if minWc is not None:
            books = books.filter(Q(wc_ar__gte=minWc) | Q(wc_lex__gte=minWc))

        if maxWc is not None:
            books = books.filter(Q(wc_ar__lte=maxWc) | Q(wc_lex__lte=maxWc))

        if minLex is not None:
            books = books.filter(Q(lexile_ar__gte=minLex) | Q(lexile_lex__gte=minLex))

        if maxLex is not None:
            books = books.filter(Q(lexile_ar__lte=maxLex) | Q(lexile_lex__lte=maxLex))

        # Exclude books that are currently rented
        rented_book_ids = BookRentalModel.objects.filter(returned_at__isnull=True).values_list('book_inventory__book', flat=True)
        books = books.exclude(id__in=rented_book_ids)
        # Exclude books that are reserved for a lecture on the same date
        if lecture_date is not None:
            reserved_book_ids = BookReservationModel.objects.filter(lecture__date=lecture_date).values_list('books__book', flat=True)
            reserved_book_ids = [id for id in reserved_book_ids if id is not None]
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
    
    def resolve_student_book_record(self, info, student_id):
        book_records = BookRecordModel.objects.filter(student_id=student_id)
        return book_records

    def resolve_student_plbn_record(self, info, student_id, plbn):
        try:
            target_book = BookInventoryModel.objects.get(plbn=plbn)
        except BookInventoryModel.DoesNotExist:
            raise Exception("해당 plbn을 가진 도서가 없습니다.")

        book_records = BookRecordModel.objects.filter(student_id=student_id, book=target_book.book)
        return book_records.exists()  # True 또는 False 반환

    def resolve_student_book_record_with_pkg(self, info, student_id, f_nf):
        book_records = BookRecordModel.objects.filter(student_id=student_id)
        # fnf 값을 기반으로 모델 선택
        model_to_use = RecommendFictionModel if f_nf == '1' else RecommendNonFictionModel
        
        try:
            # 최신의 추천 도서 패키지 정보 가져오기
            latest_f = model_to_use.objects.filter(student__user__id=student_id).latest('created_at')
        except model_to_use.DoesNotExist:
            raise Exception('기존에 선정된 추천 도서 패키지가 없습니다.')
        
        # bookRecord와 pkg 정보를 함께 반환
        return {
            'book_records': book_records,
            'book_pkg': latest_f
        }
    
    def resolve_all_book_record(self, info):
        book_records = BookRecordModel.objects.all()
        return book_records
    
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
    
    def resolve_get_student_lecture_history(self, info, academyId, studentId):
        lectures = LectureModel.objects.filter(academy=academyId).values_list('id', flat=True)
        students_attendance = AttendanceModel.objects.filter(Q(lecture__id__in=lectures) & Q(student__user_id=studentId) )
        return students_attendance
    
    def resolve_get_lecture_memo(self, info, lectureId):
        lecture = LectureModel.objects.get(id=lectureId)
        students_attendance = AttendanceModel.objects.filter(lecture=lecture)
        return students_attendance

    def resolve_get_lecture_memo_by_student(self, info, studentId, academyIds):
        student = StudentProfileModel.objects.get(user__id = studentId)
        students_attendance = AttendanceModel.objects.filter(student=student, lecture__academy__id__in=academyIds).distinct()
        return students_attendance

    def resolve_get_customattendance(self, info, academyId, date, entryTime, endTime):
        lectures = LectureModel.objects.filter(academy=academyId, date=date, end_time=endTime)
        students_attendance = AttendanceModel.objects.filter(lecture__in=lectures).exclude(status__in=['completed', 'cancelled', 'absent','makeup'])
        target = []
        for attendance in students_attendance:
            allowed_difference = timedelta(seconds=1)
            datetime_obj = datetime.strptime(str(attendance.entry_time), "%Y-%m-%d %H:%M:%S%z").replace(tzinfo=None)
            datetime2 = datetime.strptime(entryTime, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=None)
            time_difference = abs(datetime_obj - datetime2)
            if time_difference <= allowed_difference:
                target.append(attendance.student)
        return target
    
    # 도서대여
    def resolve_get_student_rental_status(self, info, student_id, book_id):
        # `BookReservationModel`에서 해당 학생의 모든 예약을 조회합니다.
        student  = StudentProfileModel.objects.get(user__id=student_id)
        status  = BookRentalModel.objects.filter(student=student)
        result = {}
        if(book_id):
            books = BookRentalModel.objects.filter(book_inventory=book_id)
            result.book_status = books
        result.status = status
        return result
    
    # 학습 리포트
    def resolve_get_summary_report(self, info, student_id, date):
        try:
            return SummaryReportModel.objects.get(student__user__id=student_id, base_date=date)
        except SummaryReportModel.DoesNotExist:
            return None
    
    def resolve_get_month_reports(self, info, student_id, date):
        # 문자열로 받은 date 값을 datetime 객체로 변환
        date_format = "%Y-%m-%d"  # 예상되는 date 문자열의 형식
        input_date = datetime.strptime(date, date_format)
        # 입력된 날짜에서 6개월 전의 날짜를 계산
        six_months_ago = input_date - timedelta(days=6*30)  # 한 달을 30일로 가정
        
        # 쿼리를 실행하여 원하는 데이터를 가져옵니다.
        return MonthReportModel.objects.filter(
            student__user__id=student_id,
            update_time__gte=six_months_ago
        ).order_by('-update_time')  # 최근 데이터부터 정렬
    
    def resolve_get_opinion(self,info,student_id,user_id, date):
        try:
            student = StudentProfileModel.objects.get(user__id = student_id)
            user = UserModel.objects.get(id = user_id)
        except (StudentProfileModel.DoesNotExist, UserModel.DoesNotExist):
            raise Exception("student or user not found.")    
        
        academies = []
        
        # 학생 카테고리인 경우
        if hasattr(user, 'student'):
            academies.extend(list(user.student.academies.all()))

        # 선생님 카테고리인 경우
        if hasattr(user, 'teacher'):
            if user.teacher.academy:
                academies.append(user.teacher.academy)

        # 매니저 카테고리인 경우
        if hasattr(user, 'manager'):
            academies.extend(list(user.manager.academies.all()))

        # 퍼플(슈퍼유저) 카테고리인 경우
        if hasattr(user, 'superuser'):
            academies.extend(list(user.superuser.academies.all()))
        
        # 로그인한 사용자의 아카데미가 writer의 아카데미에 속해있는 Opinion만 필터링
        opinions = OpinionModel.objects.filter(student=student,date=date).filter(
            Q(writer__teacher__academy__in=academies) |
            Q(writer__student__academies__in=academies) |
            Q(writer__manager__academies__in=academies)
        ).distinct()
        
        if not opinions.exists():
            raise Exception("작성된 종합의견이 존재하지 않습니다.")
        
        return opinions
    
    def resolve_get_recommend_books(self, info, student_id, academy_id, f_nf, is_selected):
        # f_nf 값에 따라 사용할 모델을 결정
        model_to_use = RecommendFictionModel if f_nf == '1' else RecommendNonFictionModel

        try:
            latest_recommendation = model_to_use.objects.filter(student__user__id=student_id).latest('created_at')
        except model_to_use.DoesNotExist:
            return []
        
        selected_books_list = latest_recommendation.selected_books.all()

        # is_selected가 True인 경우이고 선정된 도서가 잇을 경우 이미 선정된 도서를 반환
        if is_selected and selected_books_list.exists():
            all_books_in_inventory = BookInventoryModel.objects.filter(book__in=selected_books_list, academy_id=academy_id)
            unavailable_inventory_items = set(BookReservationModel.objects.filter(books__in=all_books_in_inventory).values_list('books', flat=True))
            unavailable_inventory_items.update(BookRentalModel.objects.filter(book_inventory__in=all_books_in_inventory, returned_at__isnull=True).values_list('book_inventory', flat=True))
            inventory_items = [inventory_item for inventory_item in all_books_in_inventory if inventory_item.id not in unavailable_inventory_items]
            
            selected_books = set()  # 중복 체크를 위한 set

            for inventory_item in inventory_items:
                if inventory_item.book.id in selected_books:
                    continue  # 이미 선택된 도서는 건너뜁니다.

                if inventory_item.id not in unavailable_inventory_items:
                    inventory_item.is_available = True
                else:
                    inventory_item.is_available = False

                selected_books.add(inventory_item.book.id)  # 선택된 도서의 ID를 추가
            
            return inventory_items
        
        # is_selected가 False인 경우, 새로운 도서를 뽑는 로직을 실행
        recommended_pkgs = latest_recommendation.pkg
        recommended_pkgs = BookPkgModel.objects.filter(name=recommended_pkgs, fnf=f_nf)
        all_selected_books_inventory = []
        read_books = BookRecordModel.objects.filter(student__user__id=student_id).values_list('book', flat=True)

        for recommended_pkg in recommended_pkgs:
            recommended_books = recommended_pkg.books.all() if recommended_pkg.il == '0' else recommended_pkg.books.filter(il=recommended_pkg.il)
            # matching_books에서 학생이 읽은 도서들을 제외합니다.
            recommended_books = recommended_books.exclude(id__in=read_books)
            # BookInventory에서 선택된 도서들이 존재하는지 확인
            all_books_in_inventory = BookInventoryModel.objects.filter(book__in=recommended_books, academy_id=academy_id)
            # 예약되거나 렌탈된 도서의 인벤토리 항목을 제외
            unavailable_inventory_items = set(BookReservationModel.objects.filter(books__in=all_books_in_inventory).values_list('books', flat=True))
            unavailable_inventory_items.update(BookRentalModel.objects.filter(book_inventory__in=all_books_in_inventory, returned_at__isnull=True).values_list('book_inventory', flat=True))
            
            # 무조건 예약되거나 렌탈된 도서의 인벤토리 항목을 제외 해서 도서를 뽑아주는 경우 
            # available_inventory_items = [inventory_item for inventory_item in all_books_in_inventory if inventory_item.id not in unavailable_inventory_items]

            # 예약 가능한 추천 도서가 있을 경우 최대 il_count 만큼 도서를 뽑아서 반환
            # if available_inventory_items:
            #     count_to_sample = min(recommended_pkg.il_count, len(available_inventory_items))
            #     selected_books_inventory = sample(list(available_inventory_items), count_to_sample)
            #     all_selected_books_inventory.extend(selected_books_inventory)

            # 예약 가능한 도서와 예약 불가능한 도서를 구분해서 보내주는 경우
            available_inventory_items = []
            unavailable_inventory_items_list = []

            selected_books = set()  # 중복 체크를 위한 set

            for inventory_item in all_books_in_inventory:
                if inventory_item.book.id in selected_books:
                    continue  # 이미 선택된 도서는 건너뜁니다.

                if inventory_item.id not in unavailable_inventory_items:
                    inventory_item.is_available = True
                    available_inventory_items.append(inventory_item)
                else:
                    inventory_item.is_available = False
                    unavailable_inventory_items_list.append(inventory_item)

                selected_books.add(inventory_item.book.id)  # 선택된 도서의 ID를 추가

            inventory_num = len(selected_books)

            # 예약 가능한 도서를 우선적으로 il_count 만큼 뽑습니다.
            count_to_sample = min(recommended_pkg.il_count, len(available_inventory_items))
            selected_books_inventory = sample(available_inventory_items, count_to_sample)
            all_selected_books_inventory.extend(selected_books_inventory)

            # 나머지 il_count 만큼 예약 불가능한 도서를 뽑습니다.
            remaining_count = recommended_pkg.il_count - len(selected_books_inventory)
            if remaining_count > 0:
                selected_unavailable_books_inventory = sample(unavailable_inventory_items_list, min(remaining_count, len(unavailable_inventory_items_list)))
                all_selected_books_inventory.extend(selected_unavailable_books_inventory)
        if all_selected_books_inventory:
            selected_books = [inventory_item.book for inventory_item in all_selected_books_inventory]
            latest_recommendation.selected_books.set(selected_books)

            all_selected_books_inventory[0].temp_inventory_num = inventory_num
            return all_selected_books_inventory
        else:
            return []     
        
class Mutation(graphene.ObjectType):
    createUser = CreateUser.Field()
    create_student_profile = CreateStudentProfile.Field()
    create_remark = CreateRemark.Field()
    create_teacher_profile = CreateTeacherProfile.Field()
    create_manager_profile = CreateManagerProfile.Field()

    login = Login.Field()
    refreshToken = RefreshToken.Field()
    
    updateUser = UpdateUser.Field()
    updateAcademy = UpdateAcademy.Field()
    updateStudentProfile = UpdateStudentProfile.Field()
    updateManagerProfile = UpdateManagerProfile.Field()
    updateTeacherProfile = UpdateTeacherProfile.Field()

    add_academy_to_user = AddAcademyToUser.Field()
    update_academy_to_user = UpdateAcademyToUser.Field()
    remove_academy_from_user = RemoveAcademyFromUser.Field()

    create_lecture = CreateLecture.Field()
    create_makeup = CreateMakeup.Field()

    update_lecture_info = UpdateLectureInfo.Field()
    update_lecture = UpdateLecture.Field()
    update_lecture_students = UpdateLectureStudents.Field()

    delete_lecture_info = DeleteLectureInfo.Field()
    delete_lecture = DeleteLecture.Field()

    add_students_to_lecture = AddStudentsToLecture.Field()
    update_teacher_in_lecture = UpdateTeacherInLecture.Field()
    remove_student_from_lecture_info = RemoveStudentFromLectureInfo.Field()
    remove_student_from_lecture = RemoveStudentFromLecture.Field()
    
    create_attendance = CreateAttendance.Field()
    create_lecture_memo = CreateLectureMemo.Field()
    reserve_books = BookReservation.Field()
    reserve_plbn = PlbnReservation.Field()

    delete_book_reservations = DeleteBookReservations.Field()
    delete_lecture_book_reservations = DeleteLectureBookReservations.Field()
    delete_student_book_reservations = DeleteStudentBookReservations.Field()

    book_inventory_update = BookInventoryUpdate.Field()
    add_book_inventory = AddBookInventory.Field()
    delete_book_inventory = DeleteBookInventory.Field()

    recommend_book_by_record = RecommendBookByRecord.Field()
    recommend_book_by_period = RecommendBookByPeriod.Field()

    create_opinion = CreateOpinion.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

