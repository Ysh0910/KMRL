from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from .models import TestImage
from rest_framework.permissions import IsAuthenticated
# Create your views here.

  
class TestImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.erros, status=400)
    
    
        
    def get(self, request, *args, **kwargs):
        try:
            images = TestImage.objects.all()
            serializer = ImageIdSerializer(images, many = True)
            return Response(serializer.data)
        except:
            return Response({'error':'no ids'})

class TestImageDetailView(APIView):
    
    def get(self, request,pk, *args, **kwargs):
        try:
            print("user is",request.user)
            image = TestImage.objects.get(pk=pk)
            serializer = ImageSerializer(image)
            return Response(serializer.data)
        except:
            return Response({'error':'Invalid request'}, status=400)
        
class ImageDeleteView(APIView):
    def post(self, request, pk, *args, **kwargs):
        try:
            image = TestImage.objects.get(pk = pk)
            image.image.delete(save=False)
            image.delete()
            return Response({'message':'Image deleted successfully'}, status=201)
        except:
            return Response({'error':'image not found'}, status=404)
        

class FitnessUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = FitnessUploadSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = 201)
        return Response(serializer.errors, status=400)