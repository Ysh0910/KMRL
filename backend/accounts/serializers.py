from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *
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

class MaintenanceSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = ['id','train', 'date_start','status']

class BrandingContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandingContract
        fields = ['id', 'start_date', 'end_date','revenue', 'impressions']