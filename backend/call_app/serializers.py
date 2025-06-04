# CALLI/backend/call_app/serializers.py

from rest_framework import serializers
from .models import Booking, CallLog

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__' # Includes all fields from the Booking model

class CallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallLog
        fields = '__all__' # Includes all fields from the CallLog model