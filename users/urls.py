from django.urls import path

from users.views import CreateUserView


urlpatterns = [
    path("register/", CreateUserView.as_view(), name="register"),
]

app_name = "users"
