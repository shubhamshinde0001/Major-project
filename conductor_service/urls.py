from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.conductor_dashboard, name='conductor_dashboard'),
    path('manual-booking/', views.manual_booking, name='manual_booking'),
    path('ticket-success/<int:booking_id>/', views.conductor_ticket_success, name='conductor_ticket_success'),
    path('scan-qr/', views.scan_qr, name='scan_qr'),  # This is the scanner UI page
    path('verify-ticket/', views.verify_ticket, name='verify_ticket'),
    path('todays-bookings/', views.todays_bookings, name='todays_bookings'),
path('booking-analysis/', views.booking_analysis, name='booking_analysis'),
]
