from django.contrib import admin

# Register your models here.
# support/admin.py

from .models import Message

admin.site.register(Message)