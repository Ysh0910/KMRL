from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from django.views import View
from .models import *
from rest_framework.permissions import IsAuthenticated
import csv
import requests
from django.shortcuts import render
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
        reader = csv.DictReader(open('new_mileage_balancing.csv'))
        for row in reader:
            objs.append(Mileage(
                train = Train(train_id = row['Train ID']),
                total_kilometers = row['Total Kilometers'],
                kilometers_ran_since_last_maintenance = row['Kilometers Since Last Maintenance'],
                average_daily_kilometeres = row['Average Daily Kilometers'],
                total_mileage_for_the_period = row['Target Mileage for the period']
            ))
        Mileage.objects.bulk_create(objs)
        return Response({'message':'Mcertificates uploaded succesfully'})

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
    
class SendMileage(APIView):
    def get(self, request, *args, **kwargs):
        serializer = MileageSendSerializer(Mileage.objects.all(), many = True)
        return Response(serializer.data)
    
class Activate(View):
    def get(self, request, ud, token, *args, **kwargs):
        requests.post('http://localhost:8000/auth/users/activation/', data = {'uid':ud, 'token':token})
        return render(request, 'accounts/verfication_successfull.html', context={})