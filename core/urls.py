from django.urls import path
#from django.contrib.auth.views import LoginView, LogoutView
from . import views
from core.views import *

urlpatterns = [
    path('', views.home, name='home'),
    path('login/signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('book-ticket/', views.book_ticket_view, name='book_ticket'),
    path('booking-confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('track/<str:bus_id>/', views.track_bus, name='track_bus'),  # Add tracking view
    path('api/bus_locations/', views.all_bus_locations_api, name='all_bus_locations'),
    path('api/bus_locations/<str:bus_id>/', views.bus_locations_api, name='bus_locations_api'),  # API endpoint
    path('lost-and-found/report/', views.report_lost_item, name='report_lost_item'),
    path('lost-and-found/<int:lost_item_id>/', views.lost_and_found_confirmation, name='lost_and_found_confirmation'),
    path('complaint/report/', views.report_complaint, name='report_complaint'),
    path('complaint/<int:complaint_id>/', views.complaint_confirmation, name='complaint_confirmation'),
    path('api/routes/', views.get_routes, name='get_routes'),
    path('api/stops/', views.get_all_stops, name='get_all_stops'),
    path('api/stops/<str:route_no>/', views.get_route_stops, name='get_route_stops'),
    path('api/available-buses/', views.available_buses_from_stop),
    path('create-order/', views.create_order, name='create_order'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('api/recent-bookings/', views.get_recent_bookings, name='recent_bookings'),
    path('profile/', views.profile, name='profile'),
    path('services/', views.services, name='services'),
    path('team/', views.team, name='team'),

    path('contact/', views.contact, name='contact'),
    path('api/update-location/', views.update_location, name='update_location'),
]