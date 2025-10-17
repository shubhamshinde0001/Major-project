from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import (
    Bus, Schedule, Booking, Route, BusStop, RouteStop, Location
)
from .models import ConductorProfile, ActiveTrip, BusLocation
from .forms import ConductorSignupForm, ConductorLoginForm

import json


# -------------------- AUTH --------------------

def conductor_signup(request):
    """Signup new conductor and auto-generate Employee ID."""
    if request.method == 'POST':
        form = ConductorSignupForm(request.POST, request.FILES)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            first_name, *last_name = full_name.split(' ', 1)
            last_name = last_name[0] if last_name else ''

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            employee_id = f"C{1000 + user.id}"

            profile = form.save(commit=False)
            profile.user = user
            profile.employee_id = employee_id
            profile.save()

            messages.success(request, f"Signup successful! Your Employee ID is {employee_id}. Use this ID to log in.")
            return redirect('conductor_login')
    else:
        form = ConductorSignupForm()

    return render(request, 'signupc.html', {'form': form})


def conductor_login(request):
    """Login conductor with employee_id and password."""
    if request.method == 'POST':
        form = ConductorLoginForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            password = form.cleaned_data['password']

            try:
                profile = ConductorProfile.objects.get(employee_id=employee_id)
                user = authenticate(request, username=profile.user.username, password=password)
                if user:
                    login(request, user)
                    messages.success(request, f"Welcome, {user.first_name}!")
                    return redirect('conductor_dashboard')
                else:
                    messages.error(request, "Invalid credentials.")
            except ConductorProfile.DoesNotExist:
                messages.error(request, "Employee ID not found.")
    else:
        form = ConductorLoginForm()

    return render(request, 'loginc.html', {'form': form})


def conductor_logout(request):
    """Logout conductor."""
    logout(request)
    return redirect('conductor_login')


# -------------------- DASHBOARD --------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import Bus, Schedule, ActiveTrip
@csrf_exempt
def conductor_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('conductor_login')

    profile = request.user.conductor_profile
    active_trip = ActiveTrip.objects.filter(conductor=profile, is_active=True).first()

    # ✅ Only fetch buses and schedules when no active trip
    buses = Bus.objects.all() if not active_trip else []
    schedules = Schedule.objects.all() if not active_trip else []

    context = {
        'active_trip': active_trip,
        'buses': buses,
        'schedules': schedules,
    }

    return render(request, 'home_dashboard.html', context)


# -------------------- TRIP MANAGEMENT --------------------

def set_trip(request):
    """Start a new trip for a conductor."""
    if not request.user.is_authenticated:
        return redirect('conductor_login')

    profile = request.user.conductor_profile

    if request.method == 'POST':
        bus_id = request.POST.get('bus')
        schedule_id = request.POST.get('schedule')

        bus = get_object_or_404(Bus, id=bus_id)
        schedule = get_object_or_404(Schedule, id=schedule_id)

        # End any previous trip
        ActiveTrip.objects.filter(conductor=profile, is_active=True).update(is_active=False, ended_at=timezone.now())

        # Start a new trip
        ActiveTrip.objects.create(conductor=profile, bus=bus, schedule=schedule, is_active=True, started_at=timezone.now())

        # Update profile assignment
        profile.assigned_bus = bus
        profile.assigned_schedule = schedule
        profile.save()

        messages.success(request, f"Trip started for Bus {bus.bus_id} on Schedule {schedule}.")
        return redirect('conductor_dashboard')

    return redirect('conductor_dashboard')


def end_trip(request):
    """End active service."""
    if not request.user.is_authenticated:
        return redirect('conductor_login')

    profile = request.user.conductor_profile
    ActiveTrip.objects.filter(conductor=profile, is_active=True).update(is_active=False, ended_at=timezone.now())

    profile.assigned_bus = None
    profile.assigned_schedule = None
    profile.save()

    messages.info(request, "Service ended successfully.")
    return redirect('conductor_dashboard')


# -------------------- LOCATION UPDATES --------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_bus_location(request):
    """Receive live location from conductor and update bus location."""
    try:
        conductor = ConductorProfile.objects.get(user=request.user)
        bus = conductor.assigned_bus
        if not bus:
            return Response({"error": "No bus assigned."}, status=400)

        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        if not lat or not lng:
            return Response({"error": "Missing coordinates."}, status=400)

        location, _ = BusLocation.objects.get_or_create(bus=bus)
        location.latitude = lat
        location.longitude = lng
        location.save()

        return Response({"status": "updated", "bus_id": bus.bus_id})
    except ConductorProfile.DoesNotExist:
        return Response({"error": "Conductor profile not found"}, status=404)


# -------------------- BOOKINGS --------------------

def manual_booking(request):
    """Allow conductor to book tickets manually."""
    routes = Route.objects.all()
    bus_stops = BusStop.objects.all()

    if request.method == 'POST':
        route_no = request.POST.get('route_no')
        from_stop = request.POST.get('from_stop')
        to_stop = request.POST.get('to_stop')
        seats = int(request.POST.get('seats', 1))
        user = request.user if request.user.is_authenticated else None
        selected_route = Route.objects.filter(route_no=route_no).first()

        if from_stop and to_stop and selected_route:
            fare = selected_route.distance * 1.0 * seats

            booking = Booking.objects.create(
                user=user,
                route=route_no,
                source=from_stop,
                destination=to_stop,
                schedule=None,
                seats=seats,
                fare=fare,
                created_by_conductor=True
            )
            return redirect('conductor_ticket_success', booking_id=booking.id)

    return render(request, 'home_dashboard.html', {
        'routes': routes,
        'bus_stops': bus_stops,
        'base_fare': 30,
        'route_data': json.dumps(list(routes.values('route_no', 'distance')))
    })


def conductor_ticket_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'ticket_success.html', {'booking': booking})


@csrf_exempt
def verify_ticket(request):
    """Scan QR ticket and mark as used."""
    qr_data = request.GET.get("data")
    try:
        booking = Booking.objects.get(id=qr_data)
        if booking.used:
            return JsonResponse({"valid": False, "message": "Ticket already used"})

        booking.used = True
        booking.verified_by_conductor = True
        booking.save()

        return JsonResponse({
            "valid": True,
            "booking_id": booking.id,
            "route": booking.route,
            "source": booking.source,
            "destination": booking.destination,
            "seats": booking.seats,
            "fare": str(booking.fare),
            "message": "Ticket valid and now marked as used"
        })
    except Booking.DoesNotExist:
        return JsonResponse({"valid": False, "message": "Ticket not found"})

def scan_qr(request):
    return render(request, 'home_dashboard.html')
# -------------------- DAILY ANALYTICS --------------------

def todays_bookings(request):
    """Return today’s bookings for dashboard."""
    today = timezone.now().date()
    bookings = Booking.objects.filter(booking_time__date=today)

    filtered = bookings.filter(Q(created_by_conductor=True) | Q(created_online=True, verified_by_conductor=True))

    data = [{
        'id': b.id,
        'route': str(b.route),
        'source': b.source,
        'destination': b.destination,
        'seats': b.seats,
        'fare': b.fare,
        'type': 'Manual' if b.created_by_conductor else 'Online',
        'time': b.booking_time.strftime("%H:%M:%S"),
    } for b in filtered]

    return JsonResponse({'bookings': data})


def booking_analysis(request):
    """Aggregate today's booking and fare data."""
    today = timezone.now().date()
    bookings = Booking.objects.filter(booking_time__date=today)
    filtered = bookings.filter(Q(created_by_conductor=True) | Q(created_online=True, verified_by_conductor=True))

    return JsonResponse({
        'total_bookings': filtered.count(),
        'total_seats': filtered.aggregate(Sum('seats'))['seats__sum'] or 0,
        'total_fare': filtered.aggregate(Sum('fare'))['fare__sum'] or 0,
        'online_count': filtered.filter(created_online=True, verified_by_conductor=True).count(),
        'manual_count': filtered.filter(created_by_conductor=True).count(),
        'date': str(today),
    })




from django.http import JsonResponse
from core.models import Route, BusStop

def api_routes(request):
    routes = Route.objects.all().values('route_no', 'source', 'destination', 'distance')
    return JsonResponse(list(routes), safe=False)

def api_stops(request):
    stops = BusStop.objects.all().values('name')
    return JsonResponse(list(stops), safe=False)
