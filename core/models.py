from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, chastyna=None, **extra_fields):
        if not username:
            raise ValueError('The Username must be set')
        user = self.model(username=username, chastyna=chastyna, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True)
    chastyna = models.ForeignKey('Chastyna', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'


class Nomenklatura(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'nomenklatura'


class Zahon(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'zahony'


class Chastyna(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    zahon = models.ForeignKey(Zahon, on_delete=models.CASCADE)

    class Meta:
        db_table = 'chastyny'


class Obladnannya(models.Model):
    nomenklatura = models.ForeignKey(Nomenklatura, on_delete=models.CASCADE)
    inventory_number = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=100)
    chastyna = models.ForeignKey(Chastyna, on_delete=models.CASCADE)

    class Meta:
        db_table = 'obladnannya'


class Vyprobuvannya(models.Model):
    RESULT_CHOICES = [
        ('пройшов', 'пройшов'),
        ('не пройшов', 'не пройшов'),
    ]
    obladnannya = models.ForeignKey(Obladnannya, on_delete=models.CASCADE)
    test_date = models.DateField()
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    next_test_date = models.DateField()
    act_url = models.TextField()

    class Meta:
        db_table = 'vyprobuvannya'


class Access(models.Model):
    LEVEL_CHOICES = [
        ('ro', 'ro'),
        ('rw', 'rw'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    zahon = models.ForeignKey(Zahon, on_delete=models.CASCADE)
    chastyna = models.ForeignKey(Chastyna, on_delete=models.CASCADE)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)

    class Meta:
        db_table = 'accesses'


class Session(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    ex_time = models.BigIntegerField()

    class Meta:
        db_table = 'sessions'
