from typing import Any, Dict

# from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# Create your serializers here.


