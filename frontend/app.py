import streamlit as st
import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey

# --- Database Setup ---
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
db_session = Session()

# --- Streamlit App ---

st.title("AI Hotel Concierge Dashboard")

# --- Sidebar for Navigation ---
page = st.sidebar.selectbox(
    "Choose a page",
    ["Voice Cloning", "Booking Management", "Call Logs", "Simulate Call"]
)

# --- Voice Cloning Page ---
if page == "Voice Cloning":
    st.header("Upload Staff Voice Sample for Cloning")
    audio_file = st.file_uploader("Upload a voice sample (WAV, MP3)", type=["wav", "mp3"])
    if audio_file and st.button("Upload"):
        files = {"file": audio_file}
        # Replace with your actual Chatterbox TTS server URL
        response = requests.post("http://localhost:8000/clone", files=files)
        if response.status_code == 200:
            st.success("Voice sample uploaded and cloned successfully!")
        else:
            st.error("Failed to upload voice sample.")

# --- Booking Management Page ---
elif page == "Booking Management":
    st.header("Manage Bookings")
    # Add new booking
    with st.form("add_booking"):
        guest_name = st.text_input("Guest Name")
        phone_number = st.text_input("Phone Number")
        check_in_date = st.text_input("Check-in Date")
        room_number = st.text_input("Room Number")
        check_out_date = st.text_input("Check-out Date")
        if st.form_submit_button("Add Booking"):
            new_booking = Booking(
                guest_name=guest_name,
                phone_number=phone_number,
                check_in_date=check_in_date,
                room_number=room_number,
                check_out_date=check_out_date
            )
            db_session.add(new_booking)
            db_session.commit()
            st.success("Booking added successfully!")
    # View bookings
    bookings = db_session.query(Booking).all()
    for booking in bookings:
        st.write(f"**Guest:** {booking.guest_name}, **Room:** {booking.room_number}, **Check-in:** {booking.check_in_date}")

# --- Call Logs Page ---
elif page == "Call Logs":
    st.header("View Call Logs")
    call_logs = db_session.query(CallLog).all()
    for log in call_logs:
        st.write(f"**Guest:** {log.guest_name}, **Type:** {log.call_type}, **Status:** {log.status}, **Time:** {log.timestamp}")

# --- Simulate Call Page ---
elif page == "Simulate Call":
    st.header("Simulate Guest Call")
    # Select a booking to call
    bookings = db_session.query(Booking).all()
    booking_options = {f"{b.guest_name} (Room {b.room_number})": b.id for b in bookings}
    selected_booking = st.selectbox("Select Booking", options=list(booking_options.keys()))
    if st.button("Start Call Simulation"):
        booking_id = booking_options[selected_booking]
        booking = db_session.query(Booking).filter_by(id=booking_id).first()
        # Here you would call your FastAPI endpoint to simulate the call
        # For demo, just log the action
        new_log = CallLog(
            booking_id=booking_id,
            guest_name=booking.guest_name,
            phone_number=booking.phone_number,
            call_type="Simulated",
            status="Completed",
            duration=30,
            timestamp="2024-06-01 12:00:00",
            audio_file="simulated_call.wav"
        )
        db_session.add(new_log)
        db_session.commit()
        st.success(f"Simulated call to {booking.guest_name} (Room {booking.room_number}) logged!")

# --- Close DB Session ---
db_session.close()
