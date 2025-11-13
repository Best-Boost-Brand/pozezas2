from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# --- Core domain models ---

class Brigade(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "core_brigade"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Detachment(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "core_detachment"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    MODE_RO = "RO"   # read-only
    MODE_RW = "RW"   # read-write
    MODE_GOD = "GOD" # admin
    MODES = (
        (MODE_RO, "Read-only"),
        (MODE_RW, "Read & Write"),
        (MODE_GOD, "Admin"),
    )
    mode = models.CharField(max_length=8, choices=MODES, default=MODE_RO)
    brigade = models.ForeignKey(Brigade, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    detachments = models.ManyToManyField(Detachment, blank=True, related_name="users")

    class Meta:
        db_table = "core_user"


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_id = models.CharField(max_length=64, db_index=True, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "core_user_session"

    def is_active(self) -> bool:
        return timezone.now() < self.expires_at


# --- New: Nomenclature (catalog of items) ---

class Nomenclature(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, db_index=True)  # "драбини" | "мотузки" | ...
    slug = models.SlugField(max_length=120, unique=True)
    unit = models.CharField(max_length=32, default="шт")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_nomenclature"
        ordering = ["category", "name"]

    def __str__(self) -> str:
        return f"{self.name} [{self.category}]"


class Equipment(models.Model):
    inventory_number = models.CharField(max_length=50)
    name = models.CharField(max_length=200)   # human readable
    type = models.CharField(max_length=50, db_index=True)  # legacy рядок для сумісності
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE, related_name="equipments")

    # Нові поля (безпечні: null/blank)
    nomenclature = models.ForeignKey(Nomenclature, null=True, blank=True, on_delete=models.SET_NULL, related_name="equipments")
    description = models.CharField(max_length=255, blank=True, default="")
    detachment = models.ForeignKey(Detachment, null=True, blank=True, on_delete=models.SET_NULL, related_name="equipments")

    class Meta:
        db_table = "core_equipment"
        unique_together = (("brigade", "inventory_number"),)
        ordering = ["inventory_number"]

    def __str__(self) -> str:
        return f"{self.inventory_number} — {self.name}"


def upload_testing_file(instance, filename: str) -> str:
    return f"acts/{instance.equipment_id}/{filename}"


class Testing(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="testings")
    date = models.DateField()
    result = models.CharField(max_length=32)  # "придатно" / "непридатно"
    next_date = models.DateField(null=True, blank=True)
    file = models.FileField(upload_to=upload_testing_file, null=True, blank=True)
    external_url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "core_testing"
        ordering = ["-date", "-id"]

    def __str__(self) -> str:
        return f"{self.equipment.inventory_number} @ {self.date}: {self.result}"
