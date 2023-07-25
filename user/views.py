from django.http import JsonResponse
from django.middleware.csrf import get_token

def get_csrf_token(request):
    if request.method == 'GET' or request.method == 'POST':
        csrftoken = get_token(request)
        return JsonResponse({'csrftoken': csrftoken})