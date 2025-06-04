# CALLI/backend/call_app/utils.py

import os
import requests
import json
from agno import Agno
from agno.agents import Agent
from agno.tasks import Task, Step
from dotenv import load_dotenv
from django.conf import settings # Import settings to access HF_TOKEN from .env

# Load environment variables from .env file (if not already loaded by Django's runserver)
# It's good practice to ensure this is loaded for scripts that might run outside the full Django context
load_dotenv()

# --- Hugging Face Token ---
# Django's settings.py should have loaded this from .env if you configured it
# However, for direct utility usage or if running a script, load_dotenv() is safer.
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable not set. Please set it to your Hugging Face API token.")

# --- Agno Agents Setup ---
# Initialize Agno. Consider configuring a proper storage backend for production.
agno_app = Agno() # Default uses in-memory for quick testing

# --- Define Agno Agents ---

class VoiceCloningAgent(Agent):
    name = "VoiceCloningAgent"
    description = "Handles voice cloning using Hugging Face models."

    @agno_app.agent_step
    async def clone_voice_hf(self, audio_file_path: str):
        # This is a placeholder. Actual Hugging Face API interaction is more complex.
        # For Chatterbox, you'd be interacting with their specific API or model.
        print(f"Attempting to clone voice from: {audio_file_path} using HF_TOKEN...")
        try:
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            # Replace with the actual Hugging Face Inference API URL for your chosen TTS/voice cloning model
            # For a more robust solution, research specific HF models for voice cloning (e.g., SpeechT5)
            # and their API usage. Chatterbox might be a separate service or model you need to host.
            HF_VOICE_CLONING_INFERENCE_API_URL = "https://api-inference.huggingface.co/models/YOUR_CHATTERBOX_VOICE_CLONING_MODEL"

            with open(audio_file_path, "rb") as f:
                response = requests.post(HF_VOICE_CLONING_INFERENCE_API_URL, headers=headers, data=f.read())
            response.raise_for_status()
            voice_id = response.json().get("voice_id", "simulated_voice_id_123")
            return {"status": "success", "voice_id": voice_id}
        except requests.exceptions.RequestException as e:
            print(f"Hugging Face voice cloning error: {e}")
            return {"status": "failed", "error": str(e)}

class CallAgent(Agent):
    name = "CallAgent"
    description = "Manages outbound calls and updates booking status."

    @agno_app.agent_step
    async def make_outbound_call(self, booking_id: int, guest_name: str, phone_number: str, call_type: str, room_number: str):
        from call_app.models import Booking, CallLog
        from django.utils import timezone # For Django DateTimeField

        print(f"Simulating {call_type} call to {guest_name} ({phone_number}) for Room {room_number}")

        duration = 60
        status = "completed"

        try:
            booking = await Booking.objects.aget(id=booking_id) # Using async ORM methods
            new_call_log = CallLog(
                booking=booking,
                guest_name=guest_name,
                phone_number=phone_number,
                call_type=call_type,
                status=status,
                duration=duration,
                timestamp=timezone.now(), # Use timezone.now() for DateTimeField
                audio_file=f"simulated_call_{booking_id}_{call_type}.mp3"
            )
            await new_call_log.asave() # Using async ORM methods

            if call_type == "confirmation":
                booking.confirmation_call_made = True
            elif call_type == "survey":
                booking.survey_completed = True
            await booking.asave() # Using async ORM methods

            return {"status": "success", "call_log_id": new_call_log.id, "booking_updated": True}
        except Booking.DoesNotExist:
            print(f"Booking with ID {booking_id} not found.")
            return {"status": "failed", "error": f"Booking {booking_id} not found."}
        except Exception as e:
            print(f"Error during call simulation and logging: {e}")
            return {"status": "failed", "error": str(e)}


class BookingManagementAgent(Agent):
    name = "BookingManagementAgent"
    description = "Handles booking-related automation and reminders."

    @agno_app.agent_step
    async def check_pending_confirmations(self):
        from call_app.models import Booking
        from datetime import date
        from django.db.models import Q

        current_date = date.today()
        # Find bookings where check-in is in the near future and confirmation call not made
        # Example: check-in date is today or in the future
        pending_bookings_queryset = Booking.objects.filter(
            confirmation_call_made=False,
            check_in_date__gte=current_date
        )
        # Convert queryset to list of dicts asynchronously
        pending_bookings_data = []
        async for booking in pending_bookings_queryset:
            pending_bookings_data.append({
                "id": booking.id,
                "guest_name": booking.guest_name,
                "phone_number": booking.phone_number,
                "check_in_date": str(booking.check_in_date),
                "room_number": booking.room_number
            })
        return pending_bookings_data

    @agno_app.agent_step
    async def get_recent_checkouts_for_survey(self):
        from call_app.models import Booking
        from datetime import date, timedelta

        current_date = date.today()
        # Example: checked out within the last 7 days and survey not completed
        seven_days_ago = current_date - timedelta(days=7)
        recent_checkouts_queryset = Booking.objects.filter(
            survey_completed=False,
            check_out_date__gte=seven_days_ago,
            check_out_date__lte=current_date # Up to and including today
        )
        # Convert queryset to list of dicts asynchronously
        recent_checkouts_data = []
        async for booking in recent_checkouts_queryset:
            recent_checkouts_data.append({
                "id": booking.id,
                "guest_name": booking.guest_name,
                "phone_number": booking.phone_number,
                "check_out_date": str(booking.check_out_date)
            })
        return recent_checkouts_data

# Register agents with Agno
agno_app.register_agent(VoiceCloningAgent)
agno_app.register_agent(CallAgent)
agno_app.register_agent(BookingManagementAgent)

# Function to run an Agno task
async def run_agno_task(task_name: str, description: str, agent_name: str, action: str, args: dict = None):
    task = Task(
        name=task_name,
        description=description,
        steps=[Step(agent=agent_name, action=action, args=args if args else {})]
    )
    result = await agno_app.run_task(task)
    return result