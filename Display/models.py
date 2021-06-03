from django.db import models
from django.contrib.auth.models import User


class UserNewsLetter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()

    def __str__(self):
        return ("{} profile".format(self.user))