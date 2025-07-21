from django.contrib import admin
from .models import Bus, BusStop, RouteStop, Route, Schedule, Booking, LostAndFound, Location, LostAndFound, Complaint, ComplaintImage
from django.contrib.auth.models import Group
from django.utils.html import format_html


def create_groups():
    Group.objects.get_or_create(name='conductor')
    Group.objects.get_or_create(name='passenger')

create_groups()

admin.site.register(Bus)
admin.site.register(Route)
admin.site.register(Schedule)
admin.site.register(Booking)
admin.site.register(LostAndFound)
admin.site.register(Location)
admin.site.register(Complaint)




class LostAndFoundAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger_name', 'contact_number', 'bus', 'route', 'status', 'reported_at', 'image_preview')
    list_filter = ('status', 'reported_at')
    search_fields = ('description', 'passenger_name', 'contact_number', 'bus__bus_id', 'route__route_no')
    readonly_fields = ('reported_at', 'image_preview')

    fieldsets = (
        (None, {
            'fields': ('user', 'passenger_name', 'contact_number', 'description', 'image', 'image_preview')
        }),
        ('Bus and Route', {
            'fields': ('bus', 'route', 'loss_datetime')
        }),
        ('Status', {
            'fields': ('status', 'reported_at')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return "No image uploaded"
    image_preview.short_description = 'Image'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('user', 'reported_at', 'image_preview')
        return self.readonly_fields
    

class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'passenger_name', 'contact_number', 'address_summary', 'description_summary', 'bus', 'route', 'status', 'created_at', 'image_count')
    list_filter = ('status', 'created_at', 'bus', 'route')
    search_fields = ('description', 'passenger_name', 'contact_number', 'address', 'bus__bus_id', 'route__route_no', 'user__username')
    readonly_fields = ('created_at', 'image_preview')
    list_editable = ('status',)  # Allow inline status editing
    list_per_page = 20  # Limit rows per page for readability

    fieldsets = (
        ('Passenger Details', {
            'fields': ('user', 'passenger_name', 'contact_number', 'address')
        }),
        ('Complaint Details', {
            'fields': ('description', 'bus', 'route')
        }),
        ('Status and Metadata', {
            'fields': ('status', 'created_at')
        }),
        ('Images', {
            'fields': ('image_preview',)
        }),
    )

    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = 'Images'

    def image_preview(self, obj):
        images = obj.images.all()
        if images:
            return format_html(''.join(['<img src="{}" style="max-height: 100px; margin-right: 10px;" />'.format(img.image.url) for img in images]))
        return "No images uploaded"
    image_preview.short_description = 'Image Preview'

    def description_summary(self, obj):
        return obj.description[:100] + ('...' if len(obj.description) > 100 else '')
    description_summary.short_description = 'Description'

    def address_summary(self, obj):
        return obj.address[:100] + ('...' if len(obj.address) > 100 else '')
    address_summary.short_description = 'Address'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'created_at', 'image_preview')
        return self.readonly_fields

@admin.register(ComplaintImage)
class ComplaintImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint', 'image')
    search_fields = ('complaint__id',)


@admin.register(BusStop)
class BusStopAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude']

@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['route', 'bus_stop', 'stop_order', 'distance_from_start']
    list_filter = ['route']
    ordering = ['route', 'stop_order']


class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_no', 'source', 'destination', 'distance']