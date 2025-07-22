from django.db import models
from django.contrib.auth.models import AbstractUser

class Brigade(models.Model):
    name = models.CharField(max_length=100)

class Detachment(models.Model):
    name = models.CharField(max_length=100)
    brigade = models.ForeignKey(
        Brigade,
        on_delete=models.CASCADE,
        related_name='detachments'
    )
    users = models.ManyToManyField(
        'User', related_name='detachments', blank=True
    )

class User(AbstractUser):
    MODE_CHOICES = [
        ('GOD', 'God mode'),
        ('RW', 'Read/Write'),
        ('RO', 'Read Only'),
    ]
    mode = models.CharField(max_length=3, choices=MODE_CHOICES, default='RO')
    brigade = models.ForeignKey(
        Brigade, null=True, blank=True, on_delete=models.SET_NULL
    )

class UserSession(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sessions'
    )
    session_id = models.CharField(max_length=64, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField()

class Equipment(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)

class Testing(models.Model):
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    tested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    tested_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('brigade', 'equipment', 'tested_at')