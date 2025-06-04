import streamlit as st
import requests
from sqlalchemy import create_engine, select # Still needed if you interact with hotel.db directly from frontend
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
import json
from datetime import datetime

# --- Database Setup (Keep if you still want Streamlit to read from hotel.db directly) ---
# Note: Ideally, all DB interaction should go through your backend (Django)
Base = declarative_base()

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True)
    guest_name = Column(String)
    phone_number = Column(String)
    check_in_date = Column(String)
    room_number = Column(String)
    confirmation_call_made = Column(Boolean, default=False)
    survey_completed = Column(Boolean, default=False)
    check_out_date = Column(String)

class CallLog(Base):
    __tablename__ = 'call_logs'
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'))
    guest_name = Column(String)
    phone_number = Column(String)
    call_type = Column(String)
    status = Column(String)
    duration = Column(Integer)
    timestamp = Column(String)
    audio_file = Column(String)

engine = create_engine('sqlite:///hotel.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Django backend URL (assuming Django runs on 8000)
API_BASE_URL = "http://localhost:8000/api" # Updated to include /api/ prefix

# --- Streamlit App ---
st.set_page_config(page_title="AI Hotel Concierge Dashboard", layout="wide")
st.title("🏨 AI Hotel Concierge Dashboard")

# --- Sidebar for Navigation ---
page = st.sidebar.selectbox(
    "Choose a page",
    ["🎤 Voice Cloning", "📋 Booking Management", "📞 Call Logs", "🔄 Simulate Call", "🧠 Agno Workflows"] # Renamed n8n to Agno
)

# --- Voice Cloning Page ---
if page == "🎤 Voice Cloning":
    st.header("Upload Staff Voice Sample for Cloning")
    
    st.info("Upload a clear voice sample (10-30 seconds) of hotel staff for voice cloning. HF_TOKEN must be set in backend.") # Updated info
    
    audio_file = st.file_uploader("Upload a voice sample (WAV, MP3)", type=["wav", "mp3"])
    
    if audio_file and st.button("🎵 Clone Voice"):
        with st.spinner("Processing voice sample..."):
            # Ensure file is sent as bytes, with a filename and content type
            files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)} 
            try:
                response = requests.post(f"{API_BASE_URL}/clone-voice/", files=files) # Added trailing slash
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Voice cloned successfully! Voice ID: {result['voice_id']}")
                    st.balloons()
                else:
                    st.error(f"❌ Failed to clone voice: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: Make sure Django server is running on port 8000") # Updated error message

# --- Booking Management Page ---
elif page == "📋 Booking Management":
    st.header("Manage Hotel Bookings")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("➕ Add New Booking")
        with st.form("add_booking"):
            guest_name = st.text_input("Guest Name", placeholder="John Doe")
            phone_number = st.text_input("Phone Number", placeholder="+1-555-0123")
            check_in_date = st.date_input("Check-in Date")
            room_number = st.text_input("Room Number", placeholder="101")
            check_out_date = st.date_input("Check-out Date")
            
            if st.form_submit_button("📝 Add Booking"):
                booking_data = {
                    "guest_name": guest_name,
                    "phone_number": phone_number,
                    "check_in_date": str(check_in_date),
                    "room_number": room_number,
                    "check_out_date": str(check_out_date)
                }
                
                try:
                    response = requests.post(f"{API_BASE_URL}/bookings/", json=booking_data) # Added trailing slash
                    if response.status_code == 201: # DRF Create returns 201 Created
                        st.success("✅ Booking added successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add booking: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error("❌ Connection error: Make sure Django server is running") # Updated error message
    
    with col2:
        st.subheader("📋 Current Bookings")
        try:
            response = requests.get(f"{API_BASE_URL}/bookings/") # Added trailing slash
            if response.status_code == 200:
                bookings = response.json()
                
                if bookings:
                    for booking in bookings:
                        with st.expander(f"🏨 {booking['guest_name']} - Room {booking['room_number']}"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.write(f"📞 Phone: {booking['phone_number']}")
                                # Ensure date fields are correctly displayed (they come as strings)
                                st.write(f"📅 Check-in: {booking['check_in_date']}")
                                st.write(f"📅 Check-out: {booking['check_out_date']}")
                            with col_b:
                                st.write(f"✅ Confirmation Call: {'Done' if booking['confirmation_call_made'] else 'Pending'}")
                                st.write(f"📊 Survey: {'Completed' if booking['survey_completed'] else 'Pending'}")
                else:
                    st.info("No bookings found")
            else:
                st.error("Failed to fetch bookings")
        except requests.exceptions.RequestException as e:
            st.error("❌ Connection error: Make sure Django server is running") # Updated error message

# --- Call Logs Page ---
elif page == "📞 Call Logs":
    st.header("View Call History")
    
    try:
        response = requests.get(f"{API_BASE_URL}/call-logs/") # Added trailing slash
        if response.status_code == 200:
            call_logs = response.json()
            
            if call_logs:
                # Create a more detailed display
                for log in call_logs:
                    status_emoji = "✅" if log['status'] == 'completed' else "❌" if log['status'] == 'failed' else "⏳"
                    
                    with st.expander(f"{status_emoji} {log['guest_name']} - {log['call_type'].title()} Call"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"📞 Phone: {log['phone_number']}")
                            st.write(f"🔄 Type: {log['call_type']}")
                            st.write(f"📊 Status: {log['status']}")
                        with col2:
                            st.write(f"⏱️ Duration: {log['duration']} seconds" if log['duration'] is not None else "N/A")
                            # Ensure timestamp is correctly displayed (comes as string)
                            st.write(f"🕐 Time: {log['timestamp']}")
                            if log['audio_file']:
                                st.write(f"🎵 Audio: {log['audio_file']}")
            else:
                st.info("No call logs found")
        else:
            st.error("Failed to fetch call logs")
    except requests.exceptions.RequestException as e:
        st.error("❌ Connection error: Make sure Django server is running") # Updated error message

# --- Simulate Call Page ---
elif page == "🔄 Simulate Call":
    st.header("Simulate Guest Interaction")
    
    try:
        response = requests.get(f"{API_BASE_URL}/bookings/") # Added trailing slash
        if response.status_code == 200:
            bookings = response.json()
            
            if bookings:
                booking_options = {f"{b['guest_name']} (Room {b['room_number']})": b for b in bookings}
                selected_booking_key = st.selectbox("Select Booking for Call Simulation", options=list(booking_options.keys()))
                
                if selected_booking_key:
                    selected_booking = booking_options[selected_booking_key]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Booking Details")
                        st.write(f"**Guest:** {selected_booking['guest_name']}")
                        st.write(f"**Room:** {selected_booking['room_number']}")
                        st.write(f"**Phone:** {selected_booking['phone_number']}")
                        st.write(f"**Check-in:** {selected_booking['check_in_date']}")
                    
                    with col2:
                        st.subheader("🎯 Call Type")
                        call_type = st.selectbox("Select Call Type", ["confirmation", "survey", "upsell"])
                        
                        if st.button("📞 Start Call Simulation"):
                            with st.spinner("Simulating call..."):
                                call_data = {
                                    "booking_id": selected_booking['id'],
                                    "guest_name": selected_booking['guest_name'],
                                    "phone_number": selected_booking['phone_number'],
                                    "call_type": call_type,
                                    "room_number": selected_booking['room_number']
                                }
                                
                                try:
                                    response = requests.post(f"{API_BASE_URL}/calls/outbound/", json=call_data) # Added trailing slash
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success(f"✅ Call simulation completed!")
                                        st.json(result)
                                        st.balloons()
                                    else:
                                        st.error(f"❌ Call simulation failed: {response.text}")
                                except requests.exceptions.RequestException as e:
                                    st.error("❌ Connection error: Make sure Django server is running") # Updated error message
            else:
                st.info("No bookings available for simulation")
        else:
            st.error("Failed to fetch bookings")
    except requests.exceptions.RequestException as e:
        st.error("❌ Connection error: Make sure Django server is running") # Updated error message

# --- Agno Workflows Page ---
elif page == "🧠 Agno Workflows": # Renamed this page
    st.header("Agno Automation Status")
    
    st.info("This page shows the status of automated workflows orchestrated by Agno Agents. Check Django backend logs for detailed Agno status.") # Updated info
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Pending Confirmations (via Agno Agent)") # Updated text
        try:
            response = requests.get(f"{API_BASE_URL}/bookings/pending-confirmation/") # Added trailing slash
            if response.status_code == 200:
                pending = response.json()
                if pending:
                    for booking in pending:
                        st.write(f"🏨 {booking['guest_name']} - Room {booking['room_number']}")
                        st.write(f"📞 {booking['phone_number']}")
                        st.write(f"📅 Check-in: {booking['check_in_date']}")
                        st.divider()
                else:
                    st.success("✅ No pending confirmations")
            else:
                st.error("Failed to fetch pending confirmations")
        except requests.exceptions.RequestException as e:
            st.error("❌ Connection error: Make sure Django server is running") # Updated error message
    
    with col2:
        st.subheader("📊 Survey Candidates (via Agno Agent)") # Updated text
        try:
            response = requests.get(f"{API_BASE_URL}/bookings/recent-checkouts/") # Added trailing slash
            if response.status_code == 200:
                candidates = response.json()
                if candidates:
                    for booking in candidates:
                        st.write(f"🏨 {booking['guest_name']}")
                        st.write(f"📞 {booking['phone_number']}")
                        st.write(f"📅 Checked out: {booking['check_out_date']}")
                        st.divider()
                else:
                    st.success("✅ No survey candidates")
            else:
                st.error("Failed to fetch survey candidates")
        except requests.exceptions.RequestException as e:
            st.error("❌ Connection error: Make sure Django server is running") # Updated error message
    
    # Removed n8n specific status check as Agno is managed within the Django app.
    st.subheader("🔧 Backend Agno Status") # Updated text
    st.info("Agno Agents run within the Django backend. Check the backend logs for detailed Agno status.") # Updated text


# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 Hotel Voice Agent")
st.sidebar.markdown("AI-powered guest communication system")

# Status indicator in sidebar
try:
    response = requests.get(f"{API_BASE_URL}/bookings/", timeout=2) # Pointing to a new Django endpoint
    if response.status_code == 200:
        st.sidebar.success("🟢 API Connected")
    else:
        st.sidebar.error("🔴 API Error")
except:
    st.sidebar.error("🔴 API Disconnected")