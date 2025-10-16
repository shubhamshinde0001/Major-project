from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class Bus(models.Model):
    bus_id = models.CharField(max_length=10, unique=True)
    category = models.CharField(max_length=50)  # e.g., AC, Non-AC
    capacity = models.IntegerField()

    def __str__(self):
        return self.bus_id

class Route(models.Model):
    route_no = models.CharField(max_length=10, default='unknown')
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance = models.FloatField()

    def get_fare(self):
        # Example: $1 per km
        return self.distance * 1.0  # Adjust rate as needed

    def __str__(self):
        return f"{self.route_no}: {self.source} to {self.destination}"

class Schedule(models.Model):
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE)
    route = models.ForeignKey('Route', on_delete=models.CASCADE)
    departure_time = models.TimeField()
    available_seats = models.IntegerField()

    class Meta:
        unique_together = ('bus', 'route', 'departure_time')  # avoid duplicates

    def __str__(self):
        return f"{self.bus} - {self.route} at {self.departure_time}"

    def get_today_departure(self):
        today = datetime.now().date()
        return datetime.combine(today, self.departure_time)


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    route = models.CharField(max_length=100, null=True)
    source = models.CharField(max_length=100, null=True)
    destination = models.CharField(max_length=100, null=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True)
    seats = models.IntegerField()
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booking_time = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True)
    created_by_conductor = models.BooleanField(default=False)
    created_online = models.BooleanField(default=False) 
    verified_by_conductor = models.BooleanField(default=False)
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} by {self.user}"

class Location(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bus} at ({self.latitude}, {self.longitude})"

class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # Link to passenger
    description = models.TextField()  # Renamed from issue
    passenger_name = models.CharField(max_length=100, default="Unknown")
    contact_number = models.CharField(max_length=15, default="")
    address = models.TextField()
    route = models.ForeignKey('Route', on_delete=models.CASCADE, null=True)
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=20, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint {self.id} by {self.passenger_name} - {self.status}"

class ComplaintImage(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='complaint_images/')

    def __str__(self):
        return f"Image for Complaint {self.complaint.id}"

class LostAndFound(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)  # Link to passenger
    description = models.TextField()
    image = models.ImageField(upload_to='lost_and_found/', null=True, blank=True)  # Optional image
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, null=True)  # Bus where item was lost
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True)  # Route of the bus
    loss_datetime = models.DateTimeField(null=True)  # Time and date of loss
    passenger_name = models.CharField(max_length=100)  # Passenger's name
    contact_number = models.CharField(max_length=15)  # Contact number
    status = models.CharField(max_length=20, default='Reported')
    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lost Item {self.id} by {self.passenger_name} - {self.status}"
    



class BusStop(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name



class RouteStop(models.Model):
    route = models.ForeignKey('Route', on_delete=models.CASCADE, related_name='route_stops')
    bus_stop = models.ForeignKey('BusStop', on_delete=models.CASCADE)
    stop_order = models.PositiveIntegerField()  # To define the order of stops on the route
    distance_from_start = models.FloatField(help_text="Distance from the source stop in km")

    class Meta:
        ordering = ['stop_order']  # Ensures stops are always fetched in order

    def __str__(self):
        return f"{self.route.route_no} - Stop {self.stop_order}: {self.bus_stop.name}"



# models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    AGE_CHOICES = [
        ('child', '0-18'),
        ('adult', '19-55'),
        ('old', '56-120'),
    ]

    GENDER_CHOICES = [
        ('female', 'Female'),
        ('male', 'Male'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    full_name = models.CharField(max_length=100)
    age_group = models.CharField(max_length=10, choices=AGE_CHOICES)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    mobile = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username
