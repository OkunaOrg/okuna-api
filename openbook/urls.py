"""openbook URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from openbook.views import Time
from openbook_auth.views import Register, UsernameCheck, EmailCheck, Login
from openbook_user.views import GetUser

auth_patterns = [
    path('register/', Register.as_view(), name='register-user'),
    path('login/', Login.as_view(), name='login-user'),
    path('username-check/', UsernameCheck.as_view(), name='username-check'),
    path('email-check/', EmailCheck.as_view(), name='email-check'),
]

user_patterns = [
    path('', GetUser.as_view(), name='user'),
]

api_patterns = [
    path('user/', include(user_patterns)),
    path('auth/', include(auth_patterns)),
    url('time/', Time.as_view(), name='time')
]

urlpatterns = [
    path('api/', include(api_patterns)),
    url('admin/', admin.site.urls),
]

# The static helper works only in debug mode
# https://docs.djangoproject.com/en/2.1/howto/static-files/#serving-files-uploaded-by-a-user-during-development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
