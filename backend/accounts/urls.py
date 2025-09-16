from .models import TestImage
from django.urls import path
from .views import *
from .optim_v2 import TrainScheduleAPIView
app_name = 'accounts'

urlpatterns =[
    path('test-image/', TestImageView.as_view(), name = 'test-image'),
    path('test-image/image/<int:pk>/', TestImageDetailView.as_view(), name = 'test-image-individual'),
    path('test-image/delete/<int:pk>', ImageDeleteView.as_view(), name='delete-image'),
    path('getpredictions/', TrainScheduleAPIView.as_view(), name = "get_predictions"),
    path('fitness_certificates/', SendFitnessCeritificates.as_view(), name = "send_fitness_certificates"),
    path('joboards/', SendMaintenance.as_view(), name="send_maintenance"),
    path('branding/', SendB.as_view(), name="send_branding"),
    path('mileage/', SendMileage.as_view(), name = 'send_mileage')
    #path('upload/fitness', )
]

