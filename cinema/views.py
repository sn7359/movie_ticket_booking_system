from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
import razorpay
from .models import Movie, Booking
from .forms import BookingForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

# Configure Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))


# ================= HOME =================
def home(request):
    movies = Movie.objects.all().order_by('-id')
    action_movies = Movie.objects.filter(genre='ACTION')[:4]
    comedy_movies = Movie.objects.filter(genre='COMEDY')[:4]
    drama_movies = Movie.objects.filter(genre='DRAMA')[:4]

    # Trending based on view_count
    trending_movies = Movie.objects.order_by('-view_count')[:6]

    return render(request, 'cinema/home.html', {
        'movies': movies,
        'action_movies': action_movies,
        'comedy_movies': comedy_movies,
        'drama_movies': drama_movies,
        'trending_movies': trending_movies,
    })


# ================= STATIC PAGES =================
def about(request):
    return render(request, 'cinema/about.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('cinema:contact')
    return render(request, 'cinema/contact.html')


# ================= SEARCH =================
def search_movies(request):
    genre = request.GET.get('genre', '')
    query = request.GET.get('q', '')

    movies = Movie.objects.all()

    if genre:
        movies = movies.filter(genre=genre)
    if query:
        movies = movies.filter(title__icontains=query)

    return render(request, 'cinema/search.html', {
        'movies': movies,
        'search_query': query,
        'selected_genre': genre
    })


# ================= MOVIE DETAIL =================
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    
    # AI Suggestions: Same genre + different movie + order by rating
    suggestions = Movie.objects.filter(
        genre=movie.genre
    ).exclude(id=movie_id).order_by('-rating', '-view_count')[:4]
    
    return render(request, 'cinema/movie_detail.html', {
        'movie': movie,
        'suggestions': suggestions
    })


# ================= AUTH =================
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            next_url = request.POST.get('next') or request.GET.get('next', 'cinema:home')
            return redirect(next_url)
    else:
        form = UserCreationForm()

    return render(request, 'cinema/signup.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.POST.get('next') or request.GET.get('next', 'cinema:home')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'cinema/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('cinema:home')


# ================= BOOKING =================
@login_required(login_url='cinema:login')
def book_ticket(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.movie = movie

            if booking.number_of_tickets > movie.available_seats:
                messages.error(request, f'Only {movie.available_seats} seats available!')
                return render(request, 'cinema/book_ticket.html', {'form': form, 'movie': movie})

            booking.total_amount = movie.ticket_price * booking.number_of_tickets
            booking.save()

            movie.available_seats -= booking.number_of_tickets
            movie.save()

            return redirect('cinema:payment', booking_reference=booking.booking_reference)
    else:
        form = BookingForm()

    return render(request, 'cinema/book_ticket.html', {'form': form, 'movie': movie})


def booking_confirmation(request, booking_reference):
    booking = get_object_or_404(Booking, booking_reference=booking_reference)
    return render(request, 'cinema/booking_confirmation.html', {'booking': booking})


# ================= PAYMENT =================
def payment(request, booking_reference):
    print("=" * 50)
    print("PAYMENT VIEW CALLED!")
    print(f"Booking Reference: {booking_reference}")
    print(f"RAZORPAY_ID: {settings.RAZORPAY_ID[:10] if settings.RAZORPAY_ID else 'EMPTY!'}")
    print(f"RAZORPAY_SECRET exists: {bool(settings.RAZORPAY_SECRET)}")
    print("=" * 50)
    
    booking = get_object_or_404(Booking, booking_reference=booking_reference)

    amount_in_paisa = int(float(booking.total_amount) * 100)

    order_data = {
        'amount': amount_in_paisa,
        'currency': 'INR',
        'payment_capture': 1
    }

    try:
        print("Attempting to create Razorpay order...")
        razorpay_order = razorpay_client.order.create(data=order_data)
        print(f"✅ SUCCESS! Order created: {razorpay_order['id']}")
    except Exception as e:
        print(f"❌ RAZORPAY ERROR: {str(e)}")
        messages.error(request, 'Payment initialization failed. Please try again later.')
        return redirect('cinema:booking_confirmation', booking_reference=booking_reference)

    context = {
        'booking': booking,
        'razorpay_key_id': settings.RAZORPAY_ID,
        'razorpay_order_id': razorpay_order['id'],
        'amount': amount_in_paisa
    }

    print("Rendering payment.html...")
    return render(request, 'cinema/payment.html', context)


@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        booking_reference = request.POST.get('booking_reference')

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)

            booking = get_object_or_404(Booking, booking_reference=booking_reference)
            booking.payment_status = 'COMPLETED'
            booking.save()

            messages.success(request, f'Payment successful! Payment ID: {payment_id}')
            return redirect('cinema:booking_confirmation', booking_reference=booking_reference)

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, 'Payment verification failed!')
            return redirect('cinema:payment', booking_reference=booking_reference)

    return redirect('cinema:home')
