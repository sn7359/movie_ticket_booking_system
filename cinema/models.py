from django.db import models 
import uuid 
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models

# Create your models here.
class Movie(models.Model):
    GENRE_CHOICES = [
        ('ACTION', 'Action'),
        ('COMEDY', 'Comedy'),
        ('DRAMA', 'Drama'),
        ('HORROR', 'Horror'),
        ('ROMANCE', 'Romance'),
        ('SCI-FI', 'Science Fiction'),
        ('THRILLER', 'Thriller'),
        ('ANIMATION', 'Animation'),
    ]

    RATING_CHOICES = [
        ('G', 'G - General Audiences'),
        ('PG', 'PG - Parental Guidance'),
        ('PG-13', 'PG-13 - Parents Strongly Cautioned'),
        ('R', 'R - Restricted'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.IntegerField(help_text='Duration in minutes')
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES)
    release_date = models.DateField()
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    ticket_price = models.DecimalField(max_digits=6, decimal_places=2)
    available_seats = models.IntegerField(default=100)
    rating = models.CharField(max_length=10, choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    is_trending = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title 
    
    class Meta:
        ordering = ['-release_date'] 


class Booking(models.Model):
    PAYMENT_STATUS_CHOICES=[
        ('PENDING','Pending'),
        ('COMPLETED','Completed'),
        ('FAILED','Failed'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    number_of_tickets = models.IntegerField()
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    booking_date = models.DateTimeField(auto_now_add=True)
    booking_reference = models.CharField(max_length=12, unique=True, editable=False)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def save(self, *args, **kwargs):  
        # Generate booking reference if it doesn't exist
        if not self.booking_reference:
            self.booking_reference = str(uuid.uuid4().hex[:12]).upper()
        
        # Generate QR code if it doesn't exist
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # QR code data: booking reference + movie + customer info
            qr_data = f"CINEPLEX BOOKING\nRef: {self.booking_reference}\nMovie: {self.movie.title}\nCustomer: {self.customer_name}\nTickets: {self.number_of_tickets}"
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Save to model
            file_name = f'qr_{self.booking_reference}.png'
            self.qr_code.save(file_name, File(buffer), save=False)
        
        super().save(*args, **kwargs)

    def __str__(self):  
        return f"{self.booking_reference} - {self.customer_name}"

    class Meta:  
        ordering = ['-booking_date']