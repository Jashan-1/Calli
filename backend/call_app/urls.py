# CALLI/backend/call_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Bookings API
    path('bookings/', views.BookingListCreate.as_view(), name='booking-list-create'),
    # You might want a detail view later: path('bookings/<int:pk>/', views.BookingDetail.as_view(), name='booking-detail'),

    # Call Logs API
    path('call-logs/', views.CallLogList.as_view(), name='call-log-list'),

    # Voice Cloning API
    path('clone-voice/', views.clone_voice_view, name='clone-voice'),

    # Outbound Calls API
    path('calls/outbound/', views.initiate_outbound_call_view, name='initiate-outbound-call'),

    # Agno Agent Trigger Endpoints
    path('bookings/pending-confirmation/', views.get_pending_confirmations_view, name='pending-confirmations'),
    path('bookings/recent-checkouts/', views.get_recent_checkouts_view, name='recent-checkouts'),
]