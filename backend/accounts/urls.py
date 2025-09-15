from .models import TestImage
from django.urls import path
from .views import TestImageView, TestImageDetailView, ImageDeleteView
app_name = 'accounts'

urlpatterns =[
    path('test-image/', TestImageView.as_view(), name = 'test-image'),
    path('test-image/image/<int:pk>/', TestImageDetailView.as_view(), name = 'test-image-individual'),
    path('test-image/delete/<int:pk>', ImageDeleteView.as_view(), name='delete-image'),
    #path('upload/fitness', )
]