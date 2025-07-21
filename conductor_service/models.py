from django.db import models
from django.contrib.auth.models import User
from core.models import Bus, Schedule, Booking  # Assuming 'core' is your existing app

class ConductorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='conductor_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    assigned_bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"Conductor {self.user.username} ({self.employee_id})"


class CashBooking(models.Model):
    conductor = models.ForeignKey(ConductorProfile, on_delete=models.SET_NULL, null=True)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    cash_received = models.DecimalField(max_digits=10, decimal_places=2)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cash Booking {self.booking.id} by {self.conductor}"


class QRValidationLog(models.Model):
    conductor = models.ForeignKey(ConductorProfile, on_delete=models.SET_NULL, null=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    validated_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)
    location = models.CharField(max_length=255, null=True, blank=True)  # optional GPS info

    def __str__(self):
        return f"Validation of Booking {self.booking.id} by {self.conductor}"


class DailyReport(models.Model):
    conductor = models.ForeignKey(ConductorProfile, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_cash_collected = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_passengers = models.IntegerField(default=0)

    def __str__(self):
        return f"Report: {self.conductor} - {self.date}"
