from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from .models import *
from rest_framework.permissions import IsAuthenticated
import csv
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
    
class SendFitnessCertificates(APIView):
    def get(self, request, *args, **kwargs):
        objs = []
        reader = csv.DictReader(open('new_branding_priorities.csv'))
        for row in reader:
            objs.append(BrandingContract(
                train = Train(train_id = row['Train ID']),
                branding_firm = row['Advertiser'],
                start_date = row['Contract Start Date'],
                end_date = row['Contract End Date'],
                revenue = row['Revenue per Day/Run'],
                impressions = row['Impressions per Run'],
            ))
        BrandingContract.objects.bulk_create(objs)
        return Response({'message':'Bcertificates uploaded succesfully'})

# class FeedTrains(APIView):
#     def get(self, request, *args, **kwargs):
#         try:
#             objs = []
#             reader = csv.DictReader(open('new_fitness_certificates.csv'))
#             for row in reader:
#                 objs.append(Train(train_id = row['Train ID']))
#             Train.objects.bulk_create(objs)
#             return Response({"message":'trains inputed successfully'})
#         except Exception as e:
#             return Response({"error":f'some error occured {e}'}, status=400)

class SendFitnessCeritificates(APIView):
    def get(self, request, *args, **kwargs):
        serializer = FitnessSendSerializer(FitnessDepartment.objects.all(), many = True)
        return Response(serializer.data)




class SendMaintenance(APIView):
    def get(self, request, *args, **kwargs):
        serializer = MaintenanceSendSerializer(Maintenance.objects.all(), many = True)
        return Response(serializer.data)
    
class SendB(APIView):
    def get(self, request, *args, **kwargs):
        serializer = BrandingContractSerializer(BrandingContract.objects.all(), many = True)
        return Response(serializer.data)