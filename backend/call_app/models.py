# CALLI/backend/call_app/models.py

from django.db import models

class Booking(models.Model):
    guest_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    check_in_date = models.DateField()
    room_number = models.CharField(max_length=50)
    confirmation_call_made = models.BooleanField(default=False)
    survey_completed = models.BooleanField(default=False)
    check_out_date = models.DateField() # Changed to DateField for Django
    created_at = models.DateTimeField(auto_now_add=True) # Added for tracking

    def __str__(self):
        return f"{self.guest_name} - Room {self.room_number}"

class CallLog(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='call_logs')
    guest_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    call_type = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    duration = models.IntegerField(null=True, blank=True) # Duration in seconds
    timestamp = models.DateTimeField(auto_now_add=True) # Automatically sets on creation
    audio_file = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Call to {self.guest_name} ({self.call_type}) - {self.status}"