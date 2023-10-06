from celery import shared_task

@shared_task
def create_monthly_lectures():
    # auto add 일 경우 매월(1일 마다) 강의를 생성하는 로직
    print("auto add 일 경우 매월(1일 마다) 강의를 생성하는 로직")
    pass
