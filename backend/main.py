# Add these to your main.py FastAPI app

import requests
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

# n8n webhook configuration
N8N_BASE_URL = "http://localhost:5678"  # Default n8n port
N8N_WEBHOOK_URL = f"{N8N_BASE_URL}/webhook"

@app.get("/api/bookings/pending-confirmation")
async def get_pending_confirmations():
    """Get bookings that need confirmation calls"""
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    
    # Query your database for bookings checking in tomorrow
    bookings = db.get_bookings_by_checkin_date(tomorrow_str)
    
    return [
        {
            "booking_id": booking.id,
            "guest_name": booking.guest_name,
            "phone_number": booking.phone_number,
            "check_in_date": booking.check_in_date,
            "room_number": booking.room_number
        }
        for booking in bookings
        if not booking.confirmation_call_made
    ]

@app.get("/api/bookings/recent-checkouts")
async def get_recent_checkouts():
    """Get recent checkouts for survey calls"""
    week_ago = datetime.now() - timedelta(days=7)
    recent_checkouts = db.get_recent_checkouts(week_ago)
    
    return [
        {
            "booking_id": booking.id,
            "guest_name": booking.guest_name, 
            "phone_number": booking.phone_number,
            "check_out_date": booking.check_out_date,
            "survey_completed": booking.survey_completed
        }
        for booking in recent_checkouts
    ]

@app.post("/api/calls/outbound")
async def initiate_outbound_call(call_data: dict):
    """Trigger an outbound voice call"""
    try:
        # Generate the voice message
        message = generate_call_message(
            call_data["call_type"], 
            call_data["guest_name"],
            call_data.get("room_number")
        )
        
        # Create TTS audio using Chatterbox
        audio_file = await create_voice_message(message)
        
        # Simulate call (in real implementation, integrate with voice service)
        call_result = {
            "call_id": f"call_{datetime.now().timestamp()}",
            "booking_id": call_data["booking_id"],
            "guest_name": call_data["guest_name"],
            "phone_number": call_data["phone_number"],
            "call_type": call_data["call_type"],
            "status": "completed",  # or "failed", "no_answer"
            "duration": 45,  # seconds
            "timestamp": datetime.now().isoformat(),
            "audio_file": audio_file
        }
        
        # Log the call to database
        db.log_call(call_result)
        
        # Update booking status if confirmation call
        if call_data["call_type"] == "confirmation":
            db.mark_confirmation_call_made(call_data["booking_id"])
        
        return call_result
        
    except Exception as e:
        # Trigger retry workflow on failure
        await trigger_n8n_webhook("call-failed", {
            **call_data,
            "error": str(e),
            "retry_count": call_data.get("retry_count", 0)
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calls/schedule-retry")
async def schedule_call_retry(retry_data: dict):
    """Schedule a call retry with delay"""
    delay_hours = retry_data.get("retry_delay", 1)
    
    # In production, use a proper task queue like Celery
    # For simplicity, we'll use a basic in-memory scheduler
    asyncio.create_task(
        delayed_retry_call(retry_data, delay_hours * 3600)
    )
    
    return {"status": "retry_scheduled", "delay_hours": delay_hours}

@app.post("/api/calls/mark-failed") 
async def mark_call_permanently_failed(call_data: dict):
    """Mark a call as permanently failed after max retries"""
    db.mark_call_failed(call_data["booking_id"], call_data["call_type"])
    
    # Send notification to hotel staff
    await send_staff_notification(
        f"Failed to reach {call_data['guest_name']} after multiple attempts"
    )
    
    return {"status": "marked_as_failed"}

# Helper functions
async def trigger_n8n_webhook(webhook_path: str, data: dict):
    """Trigger an n8n webhook"""
    try:
        response = requests.post(
            f"{N8N_WEBHOOK_URL}/{webhook_path}",
            json=data,
            timeout=10
        )
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to trigger n8n webhook: {e}")

async def delayed_retry_call(call_data: dict, delay_seconds: int):
    """Retry a call after delay"""
    await asyncio.sleep(delay_seconds)
    
    # Remove retry-specific fields and try again
    retry_call_data = {k: v for k, v in call_data.items() 
                      if k not in ["retry_count", "retry_delay", "error"]}
    
    await initiate_outbound_call(retry_call_data)

def generate_call_message(call_type: str, guest_name: str, room_number: str = None) -> str:
    """Generate appropriate message based on call type"""
    templates = {
        "confirmation": f"Hello {guest_name}, this is calling from the hotel. We wanted to confirm your check-in tomorrow. Your room {room_number} will be ready by 3 PM. Is there anything special we can prepare for your arrival?",
        "survey": f"Hi {guest_name}, thank you for staying with us. We hope you enjoyed your visit. Could you please rate your experience from 1 to 10? Your feedback helps us improve our service.",
        "upsell": f"Hello {guest_name}, we have a special offer for spa services during your stay. Would you be interested in learning more?"
    }
    return templates.get(call_type, f"Hello {guest_name}, this is a call from the hotel.")

async def create_voice_message(text: str) -> str:
    """Create TTS audio using Chatterbox"""
    # This would integrate with your chatterbox_api.py
    # Return path to generated audio file
    return "path/to/generated/audio.wav"

async def send_staff_notification(message: str):
    """Send notification to hotel staff"""
    # Implement email/SMS notification
    pass