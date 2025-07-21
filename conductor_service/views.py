from django.shortcuts import render, redirect, get_object_or_404
from core.models import Schedule, Booking, Route
from django.utils import timezone
from core.models import *

def conductor_dashboard(request):
    return render(request, 'home_dashboard.html')

from django.shortcuts import render, redirect, get_object_or_404
from core.models import Schedule, Booking, RouteStop
from django.contrib import messages
from django.core.serializers import serialize
from django.http import JsonResponse
import json

def manual_booking(request):
    routes = Route.objects.all()
    bus_stops = BusStop.objects.all()

    if request.method == 'POST':
        route_no = request.POST.get('route_no')
        from_stop = request.POST.get('from_stop')
        to_stop = request.POST.get('to_stop')
        seats = int(request.POST.get('seats', 1))

        selected_route = Route.objects.filter(route_no=route_no).first()

        if from_stop and to_stop and selected_route:
            fare = selected_route.distance * 1.0 * seats

            booking = Booking.objects.create(
                user=None,
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



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import Booking

@csrf_exempt
def verify_ticket(request):
    qr_data = request.GET.get("data")

    try:
        booking = Booking.objects.get(id=qr_data)

        if booking.used:
            return JsonResponse({"valid": False, "message": "Ticket already used"})

        # ✅ Mark as used
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


from django.shortcuts import render, get_object_or_404
from core.models import Booking

def conductor_ticket_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'ticket_success.html', {
        'booking': booking
    })


def scan_qr(request):
    return render(request, 'home_dashboard.html')


from django.utils import timezone
from django.shortcuts import render
from core.models import Booking

def todays_bookings(request):
    today = timezone.now().date()
    bookings = Booking.objects.filter(booking_time__date=today).order_by('-booking_time')

    filtered_bookings = bookings.filter(
        models.Q(created_by_conductor=True) | models.Q(created_online=True, verified_by_conductor=True)
    )

    data = []
    for booking in filtered_bookings:
        data.append({
            'id': booking.id,
            'route': str(booking.route),
            'source': booking.source,
            'destination': booking.destination,
            'seats': booking.seats,
            'fare': booking.fare,
            'type': 'Manual' if booking.created_by_conductor else 'Online' if booking.created_online else 'Unknown',
            'time': booking.booking_time.strftime("%H:%M:%S"),
        })

    return JsonResponse({'bookings': data})

'''
    return render(request, 'home_dashboard.html', {
        'bookings': bookings,
        'today': today,
    })
'''


from django.db.models import Sum, Count
from django.shortcuts import render
from core.models import Booking
from django.utils import timezone

def booking_analysis(request):
    today = timezone.now().date()
    bookings = Booking.objects.filter(booking_time__date=today)

    filtered_bookings = bookings.filter(
        models.Q(created_by_conductor=True) | models.Q(created_online=True, verified_by_conductor=True)
    )

    total_bookings = filtered_bookings.count()
    total_seats = filtered_bookings.aggregate(total=Sum('seats'))['total'] or 0
    total_fare = filtered_bookings.aggregate(total=Sum('fare'))['total'] or 0

    online_count = filtered_bookings.filter(created_online=True, verified_by_conductor=True).count()
    manual_count = filtered_bookings.filter(created_by_conductor=True).count()

   
    return JsonResponse({
        'total_bookings': total_bookings,
        'total_seats': total_seats,
        'total_fare': total_fare,
        'online_count': online_count,
        'manual_count': manual_count,
        'date': str(today),
    })


