from  django.urls import path
from . import views

from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


urlpatterns = [
    path("signup/",view=views.register_user),
    #path("login/",view=views.login_user)
    path("login/",view=TokenObtainPairView.as_view()),
    path("token-refresh/",view=TokenRefreshView.as_view()),
    path("logout/",view=views.logout_user),
    path("addresses/", views.list_addresses),
    path("addresses/create/", views.create_address),
]