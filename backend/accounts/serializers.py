from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import TestImage, FitnessDepartment
User = get_user_model()

class ImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url = True)
    class Meta:
        model = TestImage
        fields = ['id', 'image']

class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ['id', 'email', 'name', 'password']

class ImageIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestImage
        fields = ['id']

class FitnessUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessDepartment
        fields = '__all__'

class FitnessSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessDepartment
        fields = [ 'train_id', 'signal', 'braking', 'structural_integrity', 'expiry_date']