from django.db import models

# Create your models here.



class Message(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    reply = models.TextField(blank=True, null=True)  # 👈 admin reply
    created_at = models.DateTimeField(auto_now_add=True)