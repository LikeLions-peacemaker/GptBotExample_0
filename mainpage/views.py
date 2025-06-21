from django.shortcuts import render
from rest_framework import generics
from .models import Lawyer, Reservation
from .serializers import LawyerSerializer, ReservationSerializer

# Create your views here.
# views.py

class LawyerListView(generics.ListAPIView):
    queryset = Lawyer.objects.all()
    serializer_class = LawyerSerializer

class LawyerDetailView(generics.RetrieveAPIView):
    queryset = Lawyer.objects.all()
    serializer_class = LawyerSerializer

class ReservationCreateView(generics.CreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
