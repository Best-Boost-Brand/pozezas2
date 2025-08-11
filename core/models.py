from django.contrib.auth.models import AbstractUser
from django.db import models

class Brigade(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Detachment(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    MODE_CHOICES = (
        ('RO', 'Read-Only'),
        ('RW', 'Read-Write'),
        ('GOD','Administrator'),
    )
    mode = models.CharField(max_length=3, choices=MODE_CHOICES, default='RO')
    brigade = models.ForeignKey(Brigade, on_delete=models.SET_NULL, null=True, blank=True)
    detachments = models.ManyToManyField(Detachment, blank=True)

    def __str__(self):
        return f"{self.username} [{self.mode}]"

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, unique=True)
    expires = models.DateTimeField()

    def __str__(self):
        return f"{self.user} ({self.expires})"

class Equipment(models.Model):
    inventory_number = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    # тип приладдя: "драбини", "мотузки", "рукавиці", "ремені" і т.д.
    type = models.CharField(max_length=100)
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('inventory_number', 'brigade')

    def __str__(self):
        return f"{self.name} ({self.inventory_number})"

class Testing(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='testings')
    date = models.DateField()
    result = models.CharField(max_length=100)     # "придатно" / "непридатно" і т.п.
    next_date = models.DateField()
    file = models.FileField(upload_to='acts/', null=True, blank=True)
    tested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.equipment.inventory_number} - {self.date}"
