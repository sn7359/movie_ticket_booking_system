from django.contrib import admin
from .models import Movie, Booking 

# Register your models here.
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'release_date', 'ticket_price', 'available_seats', 'rating')
    list_filter = ('genre', 'rating', 'release_date')
    search_fields = ('title', 'description')
    list_per_page = 20 
    date_hierarchy = 'release_date'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'customer_name', 'movie', 'number_of_tickets', 'total_amount', 'payment_status', 'booking_date')
    list_filter = ('payment_status','booking_date')
    search_fields = ('booking_reference','customer_name','customer_email')
    readonly_fields = ('booking_reference', 'booking_date', 'total_amount')
    list_per_page = 20 
    date_hierarchy = 'booking_date' 