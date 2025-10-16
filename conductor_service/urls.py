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
    path('signup/', views.conductor_signup, name='conductor_signup'),
    path('login/', views.conductor_login, name='conductor_login'),
    path('logout/', views.conductor_logout, name='conductor_logout'),
        path('trip/start/', views.set_trip, name='set_trip'),
    path('trip/end/', views.end_trip, name='end_trip'),
    path('api/routes/', views.api_routes, name='api_routes'),
path('api/stops/', views.api_stops, name='api_stops'),
]
