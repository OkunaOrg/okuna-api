from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from proxy.views import proxy_view

@csrf_exempt
def proxy_auth_view(request, url):
    if request.method != 'GET':
        return HttpResponse(
            'Only method GET is allowed',
            content_type='text/plain',
            status=405)

    is_authenticated = bool(request.user and request.user.is_authenticated)
    if is_authenticated:
        return proxy_view(request, url)

    return HttpResponse(
        'No authentication token found',
        content_type='text/plain',
        status=401)
