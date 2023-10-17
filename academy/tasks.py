# from backend.celery import shared_task
from datetime import datetime, timedelta
import pytz
from calendar import monthrange

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

# @shared_task
def create_monthly_lectures():
    print("auto add 일 경우 매월(1일 마다) 강의를 생성하는 코드")
    target_lecture_info = LectureInfoModel.objects.filter(auto_add = True)
    korea_timezone = pytz.timezone('Asia/Seoul')

    today = datetime.now(korea_timezone)

    # 다음 달의 첫날을 계산합니다.
    if today.month == 12:
        next_month_first_day = today.replace(year=today.year+1, month=1, day=1)
    else:
        next_month_first_day = today.replace(month=today.month+1, day=1)

    # 다음 달의 마지막 날을 계산합니다.
    _, last_day_of_next_month = monthrange(next_month_first_day.year, next_month_first_day.month)
    next_month_last_day = next_month_first_day.replace(day=last_day_of_next_month)

    for lecture_info in target_lecture_info:
        current_date = next_month_first_day
        repeat_days = lecture_info.repeat_day.get("repeat_days", [])
        
        # 기존 강의를 가져옵니다. 만약 없다면 다음 lecture_info로 넘어갑니다.
        existing_lecture = lecture_info.lectureList.all().first()
        if not existing_lecture:
            continue

        while current_date <= next_month_last_day:
            if current_date.weekday() in repeat_days:
                print(existing_lecture)
                new_lecture = LectureModel(
                    academy=existing_lecture.academy,
                    lecture_info=existing_lecture.lecture_info,
                    date=current_date,  # date 값만 변경
                    start_time=existing_lecture.start_time,
                    end_time=existing_lecture.end_time,
                    lecture_memo=existing_lecture.lecture_memo,
                    teacher=existing_lecture.teacher,
                )
                new_lecture.save()
                new_lecture.students.set(existing_lecture.students.all())

            current_date += timedelta(days=1)
