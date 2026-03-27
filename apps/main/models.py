import uuid
from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username


class Region(models.Model):
    image = models.ImageField(upload_to='regions/')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)  # Mashhur, Yaqin, Tavsiya

    def __str__(self):
        return self.name


class PlaceImage(models.Model):
    place = models.ForeignKey(
        'Place',
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(upload_to='places/')
    caption = models.CharField(max_length=255, blank=True)
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.place.title} image"


class PlaceContent(models.Model):
    place = models.ForeignKey(
        'Place',
        on_delete=models.CASCADE,
        related_name='contents'
    )

    title = models.CharField(max_length=255)  
    content = models.TextField()

    def __str__(self):
        return f"{self.place.title} - {self.title}"


class Place(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='places'
    )

    categories = models.ManyToManyField(
        Category,
        related_name='places',
        blank=True
    )

    image = models.ImageField(upload_to='places/')
    address = models.CharField(max_length=255)

    latitude = models.FloatField()
    longitude = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
