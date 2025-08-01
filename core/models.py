from django.contrib.auth.models import AbstractUser
from django.db import models

class Brigade(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Detachment(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class User(AbstractUser):
    MODE_CHOICES = (
        ('GOD', 'God'),
        ('RO', 'Read Only'),
        ('RW', 'Read Write'),
    )
    mode = models.CharField(max_length=3, choices=MODE_CHOICES, default='RO')
    brigade = models.ForeignKey(Brigade, null=True, blank=True, on_delete=models.SET_NULL)
    detachments = models.ManyToManyField(Detachment, blank=True)

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, unique=True)
    expires = models.DateTimeField()


class Equipment(models.Model):
    inventory_number = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)  # тип приладдя: драбини, мотузки тощо
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE, default=1)


    def __str__(self):
        return f"{self.name} ({self.inventory_number})"


class Testing(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='testings')
    date = models.DateField()
    result = models.CharField(max_length=100)
    next_date = models.DateField()
    file = models.FileField(upload_to='acts/', null=True, blank=True)  # ⬅️ нове поле

    def __str__(self):
        return f"{self.equipment.inventory_number} - {self.date}"

