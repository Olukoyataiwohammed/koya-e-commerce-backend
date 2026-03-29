
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    return HttpResponse("Welcome to my Django app!")


urlpatterns = [
    path('admin/', admin.site.urls),
    path("store/", include("store.urls")),
    path("",home),
    path("cart/",include("cart.urls")),
    path("auth/",include("accounts.urls")),
    path("order/",include("order.urls")),
    path("wishlist/", include("wishlist.urls")),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

