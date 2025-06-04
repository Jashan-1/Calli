# CALLI/backend/call_app/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view # For function-based API views
from rest_framework.response import Response
from .models import Booking, CallLog
from .serializers import BookingSerializer, CallLogSerializer # We'll define these
from .utils import run_agno_task # Import the utility function
import asyncio # For running async Agno tasks
from django.core.files.storage import default_storage # For saving uploaded files
from django.core.files.base import ContentFile
import os # For cleaning up temporary files

# --- Serializers (Add these to CALLI/backend/call_app/serializers.py) ---
# Create a new file: CALLI/backend/call_app/serializers.py
# This is crucial for DRF to convert models to JSON and vice versa.
# CALLI/backend/call_app/serializers.py
# from rest_framework import serializers
# from .models import Booking, CallLog

# class BookingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Booking
#         fields = '__all__'

# class CallLogSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CallLog
#         fields = '__all__'
# ---------------------------------------------------------------------

# --- Booking API Views ---
class BookingListCreate(generics.ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

# class BookingDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Booking.objects.all()
#     serializer_class = BookingSerializer

# --- Call Log API Views ---
class CallLogList(generics.ListAPIView):
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer

# --- Voice Cloning View ---
@api_view(['POST'])
async def clone_voice_view(request):
    if 'file' not in request.FILES:
        return Response({"detail": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    file_name = default_storage.save(f"temp_{uploaded_file.name}", ContentFile(uploaded_file.read()))
    file_path = default_storage.path(file_name)

    try:
        # Run the Agno task
        task_result = await run_agno_task(
            task_name="Clone Voice Task",
            description=f"Clone voice from {uploaded_file.name}",
            agent_name="VoiceCloningAgent",
            action="clone_voice_hf",
            args={"audio_file_path": file_path}
        )

        if task_result.status == "completed":
            return Response({"voice_id": task_result.output.get("voice_id")}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": f"Voice cloning failed: {task_result.error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path) # Clean up the temporary file


# --- Outbound Call Initiation View ---
@api_view(['POST'])
async def initiate_outbound_call_view(request):
    call_data = request.data
    required_fields = ["booking_id", "guest_name", "phone_number", "call_type", "room_number"]
    if not all(field in call_data for field in required_fields):
        return Response({"detail": "Missing required call data fields."}, status=status.HTTP_400_BAD_REQUEST)

    # Run the Agno task
    task_result = await run_agno_task(
        task_name=f"Outbound {call_data['call_type']} Call",
        description=f"Initiate an outbound {call_data['call_type']} call to {call_data['guest_name']}",
        agent_name="CallAgent",
        action="make_outbound_call",
        args=call_data # Pass all call data as args
    )

    if task_result.status == "completed":
        return Response(task_result.output, status=status.HTTP_200_OK)
    else:
        return Response({"detail": f"Call simulation failed: {task_result.error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Agno Agent Trigger Endpoints ---
@api_view(['GET'])
async def get_pending_confirmations_view(request):
    task_result = await run_agno_task(
        task_name="Get Pending Confirmations",
        description="Retrieve bookings awaiting confirmation calls",
        agent_name="BookingManagementAgent",
        action="check_pending_confirmations"
    )
    if task_result.status == "completed":
        return Response(task_result.output, status=status.HTTP_200_OK)
    else:
        return Response({"detail": f"Failed to fetch pending confirmations: {task_result.error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
async def get_recent_checkouts_view(request):
    task_result = await run_agno_task(
        task_name="Get Recent Checkouts for Survey",
        description="Retrieve bookings for which surveys should be sent",
        agent_name="BookingManagementAgent",
        action="get_recent_checkouts_for_survey"
    )
    if task_result.status == "completed":
        return Response(task_result.output, status=status.HTTP_200_OK)
    else:
        return Response({"detail": f"Failed to fetch survey candidates: {task_result.error}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)