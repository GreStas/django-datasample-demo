from django.urls import path
from . import views

app_name = 'datasamples'

urlpatterns = [
    path('', views.index, name='all-samples'),
    path('edit-sample/<int:pk>', views.edit_sample, name='edit-sample'),
    path('create-sample', views.create_sample, name='create-sample'),
    path('check_datasample/<int:pk>', views.check_datasample, name='check-datasample'),
]
