import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Schedule, Booking, RouteStop, Bus, Location, LostAndFound, Route, Complaint, Booking
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .forms import LostAndFoundForm, ComplaintForm, ComplaintImageFormSet

from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def home(request):
    """Dashboard after login"""
    user_profile = None
    if hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile  # Access extra info like full_name, age, etc.

    context = {
        'user': request.user,
        'profile': user_profile
    }
    return render(request, 'home.html', context)

def profile(request):
    return render(request, 'profile.html')

def contact(request):
    return render(request, 'contact.html')

def services(request):
    return render(request, 'service.html')


def team(request):
    return render(request, 'team.html')


def book_ticket_view(request):
    route_no = request.GET.get('route_no')
    from_stop = request.GET.get('from')
    to_stop = request.GET.get('to')

    context = {
        'route_no': route_no,
        'from_stop': from_stop,
        'to_stop': to_stop,
        'base_fare': 30,  # static fare for now
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    }
    return render(request, 'book_ticket.html', context)

def booking_confirmation(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    if not booking.qr_code:
        qr = qrcode.make(str(booking.id))  # You can encode booking.id or any unique data
        buffer = BytesIO()
        qr.save(buffer)
        buffer.seek(0)
        filename = f'booking_{booking.id}_qr.png'
        booking.qr_code.save(filename, File(buffer), save=True)
    return render(request, 'booking_confirmation.html', {'booking': booking})

def bus_locations_api(request, bus_id):
    bus = get_object_or_404(Bus, bus_id=bus_id)  # Use bus_id field, not pk
    # Get the latest location for the bus (or recent locations, if desired)
    locations = Location.objects.filter(bus=bus).order_by('-timestamp')[:1]  # Latest location
    data = [
        {
            'lat': location.latitude,
            'lng': location.longitude
        } for location in locations
    ]
    return JsonResponse(data, safe=False)

def track_bus(request, bus_id):
    bus = get_object_or_404(Bus, bus_id=bus_id)
    return render(request, 'track_bus.html', {'bus_id': bus.bus_id})


def all_bus_locations_api(request):
    # For each bus, get the latest location
    buses = Bus.objects.all()
    data = []

    for bus in buses:
        latest_location = Location.objects.filter(bus=bus).order_by('-timestamp').first()
        if latest_location:
            data.append({
                'id': bus.bus_id,
                'lat': latest_location.latitude,
                'lng': latest_location.longitude
            })

    return JsonResponse(data, safe=False)


def report_lost_item(request):
    if request.method == 'POST':
        form = LostAndFoundForm(request.POST, request.FILES)
        if form.is_valid():
            lost_item = form.save(commit=False)
            lost_item.user = request.user  # Link to authenticated user
            lost_item.save()
            return redirect('lost_and_found_confirmation', lost_item_id=lost_item.id)
    else:
        form = LostAndFoundForm()
    return render(request, 'report_lost_item.html', {'form': form})

def lost_and_found_confirmation(request, lost_item_id):
    lost_item = LostAndFound.objects.get(id=lost_item_id)
    return render(request, 'lost_and_found_confirmation.html', {'lost_item': lost_item})

def report_complaint(request):
    booking_id = request.GET.get('booking_id')
    if request.user.is_authenticated:
        initial = {'passenger_name': request.user.get_full_name() or request.user.username}
    else:
        initial = {'passenger_name': ''}
   
    if booking_id:
        booking = Booking.objects.get(id=booking_id, user=request.user)
        initial.update({
            'bus': booking.schedule.bus,
            'route': booking.schedule.route,
        })
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        formset = ComplaintImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            formset.instance = complaint
            formset.save()
            return redirect('complaint_confirmation', complaint_id=complaint.id)
    else:
        form = ComplaintForm(initial=initial)
        formset = ComplaintImageFormSet()
    return render(request, 'report_complaint.html', {'form': form, 'formset': formset})

def complaint_confirmation(request, complaint_id):
    complaint = Complaint.objects.get(id=complaint_id)
    return render(request, 'complaint_confirmation.html', {'complaint': complaint})


def get_routes(request):
    routes = Route.objects.all().values('route_no', 'source', 'destination')
    return JsonResponse(list(routes), safe=False)

def get_all_stops(request):
    from .models import BusStop
    stops = BusStop.objects.all().values('id', 'name')
    return JsonResponse(list(stops), safe=False)

def get_route_stops(request, route_no):
    from .models import RouteStop
    route_stops = RouteStop.objects.filter(route__route_no=route_no).select_related('bus_stop')
    
    data = [
        {'id': rs.bus_stop.id, 'name': rs.bus_stop.name}
        for rs in route_stops
    ]

    return JsonResponse(data, safe=False)


from django.http import JsonResponse
from datetime import datetime
from .models import RouteStop, Schedule

def available_buses_from_stop(request):
    from_stop = request.GET.get('from')
    to_stop = request.GET.get('to')

    if not from_stop:
        return JsonResponse({"error": "Missing 'from' parameter"}, status=400)

    # Find all routes that pass through the from_stop
    matching_from_stops = RouteStop.objects.filter(bus_stop__name__iexact=from_stop)
    route_ids = matching_from_stops.values_list('route_id', flat=True)

    # Filter out buses that already departed today
    now = datetime.now().time()
    schedules = Schedule.objects.filter(route_id__in=route_ids, departure_time__gte=now)

    results = []
    for sched in schedules:
        route_stops = sched.route.route_stops.select_related('bus_stop').order_by('stop_order')
        stop_names = [stop.bus_stop.name for stop in route_stops]

        if from_stop in stop_names:
            if to_stop:
                if to_stop in stop_names:
                    from_index = stop_names.index(from_stop)
                    to_index = stop_names.index(to_stop)

                    if from_index < to_index:
                        results.append({
                            "route_no": sched.route.route_no,
                            "from": from_stop,
                            "to": to_stop,
                            "type": sched.bus.category,
                            "time": sched.departure_time.strftime('%I:%M %p')
                        })
            else:
                results.append({
                    "route_no": sched.route.route_no,
                    "from": from_stop,
                    "to": sched.route.destination,
                    "type": sched.bus.category,
                    "time": sched.departure_time.strftime('%I:%M %p')
                })

    return JsonResponse(results, safe=False)




import razorpay
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def create_order(request):
    data = json.loads(request.body)
    amount = int(data.get("amount", 0))
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order = client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': 1})
    return JsonResponse(order)


from django.contrib.auth.models import User
#user = User.objects.first()


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        data = json.loads(request.body)

        route_no = data.get("route_no")
        from_stop = data.get("from")
        to_stop = data.get("to")
        seats = int(data.get("seats") or 1)
        fare = int(data.get("amount", 0))

        user = request.user if request.user.is_authenticated else None

        booking = Booking.objects.create(
            user=user,  # ✅ Link the booking to the logged-in user
            route=route_no,
            source=from_stop,
            destination=to_stop,
            seats=seats,
            fare=fare,
            created_online=True,
        )

        return JsonResponse({
            "message": "Booking confirmed",
            "redirect_url": reverse('booking_confirmation', kwargs={'booking_id': booking.id})
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)




from django.http import JsonResponse
from django.shortcuts import render
from .models import Booking

def my_bookings(request):
    if not request.user.is_authenticated:
        return render(request, 'booking_history.html', {'bookings': []})

    bookings = Booking.objects.filter(user=request.user).order_by('-booking_time')
    return render(request, 'booking_history.html', {'bookings': bookings})


def get_recent_bookings(request):
    if not request.user.is_authenticated:
        return JsonResponse({'recent_bookings': []})

    bookings = Booking.objects.filter(user=request.user).order_by('-booking_time')[:3]

    data = [
        {
            'route_no': booking.route,
            'from_stop': booking.source,
            'to_stop': booking.destination,
            'seats': booking.seats,
            'fare': str(booking.fare),
            'time': booking.booking_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for booking in bookings
    ]

    return JsonResponse({'recent_bookings': data})




# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import UserProfile

# ---------- SIGNUP ----------
def signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('fullname')
        age_group = request.POST.get('age')
        gender = request.POST.get('gender')
        username = request.POST.get('username')
        password = request.POST.get('password')
        mobile = request.POST.get('mobile')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        # Create user
        user = User.objects.create_user(username=username, password=password)
        # Create profile
        UserProfile.objects.create(
            user=user,
            full_name=full_name,
            age_group=age_group,
            gender=gender,
            mobile=mobile
        )

        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('login')

    return render(request, 'signup.html')


# ---------- LOGIN ----------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('home')  # Change to your main page
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html')


# ---------- LOGOUT ----------
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')



from rest_framework.decorators import api_view
from rest_framework.response import Response
from conductor_service.models import BusLocation

@api_view(['GET'])
def get_bus_location(request, bus_id):
    try:
        location = BusLocation.objects.get(bus_id=bus_id)
        return Response({
            "latitude": location.latitude,
            "longitude": location.longitude,
            "updated_at": location.updated_at
        })
    except BusLocation.DoesNotExist:
        return Response({"error": "Bus location not found"}, status=404)


# core/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Bus, Location

@csrf_exempt
def update_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            bus_id = data.get('bus_id')
            lat = data.get('latitude')
            lng = data.get('longitude')

            bus = Bus.objects.get(bus_id=bus_id)
            Location.objects.create(bus=bus, latitude=lat, longitude=lng)
            return JsonResponse({"status": "success"})
        except Exception as e:
            print("Error updating location:", e)
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
