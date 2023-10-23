# from backend.celery import shared_task
from datetime import datetime, timedelta
import pytz
from calendar import monthrange
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
from celery import shared_task

def create_lectures_for_month(lecture_info, last_lecture, start_date, end_date):
    current_date = start_date
    repeat_days = lecture_info.repeat_day.get("repeat_days", [])
    while current_date <= end_date:
        if current_date.weekday() in repeat_days:
            new_lecture = LectureModel(
                academy=last_lecture.academy,
                lecture_info=last_lecture.lecture_info,
                date=current_date,  # date 값만 변경
                start_time=last_lecture.start_time,
                end_time=last_lecture.end_time,
                lecture_memo=last_lecture.lecture_memo,
                teacher=last_lecture.teacher,
            )
            new_lecture.save()
            new_lecture.students.set(last_lecture.students.all())
        current_date += timedelta(days=1)

@shared_task
def create_monthly_lectures():
    print("auto add 일 경우 매월(1일 마다) 강의를 생성하는 코드")
    target_lecture_info = LectureInfoModel.objects.filter(auto_add=True)

    for lecture_info in target_lecture_info:
        # 가장 늦은 날짜의 강의를 찾습니다.
        last_lecture = lecture_info.lectureList.order_by('-date').first()
        if not last_lecture:
            continue

        # 가장 늦은 날짜의 다음 달 첫날을 계산합니다.
        next_month_first_day = (last_lecture.date + relativedelta(months=+1)).replace(day=1)

        # 다음 달의 마지막 날을 계산합니다.
        _, last_day_of_next_month = monthrange(next_month_first_day.year, next_month_first_day.month)
        next_month_last_day = next_month_first_day.replace(day=last_day_of_next_month)

        # 다다음 달의 첫날과 마지막 날을 계산합니다.
        two_months_later_first_day = (next_month_first_day + relativedelta(months=+1))
        _, last_day_of_two_months_later = monthrange(two_months_later_first_day.year, two_months_later_first_day.month)
        two_months_later_last_day = two_months_later_first_day.replace(day=last_day_of_two_months_later)

        # 다음 달의 강의를 생성합니다.
        create_lectures_for_month(lecture_info, last_lecture, next_month_first_day, next_month_last_day)

        # 다다음 달의 강의를 생성합니다.
        create_lectures_for_month(lecture_info, last_lecture, two_months_later_first_day, two_months_later_last_day)
