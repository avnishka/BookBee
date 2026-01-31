from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm 
from .forms import BookForm
from .models import Book, Review, Cart , UserProfile

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, "Welcome to BookBee 🐝")
        return redirect("home") 
    return render(request, "signup.html")

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required(login_url='login')
def home(request):
    books = Book.objects.filter(status='AVAILABLE') 
    return render(request, "home.html", {'books': books})

@login_required(login_url='login') 
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False) 
            book.owner = request.user       
            book.save()                    
            return redirect('home')   
    else:
        form = BookForm()
    return render(request, 'add_book.html', {'form': form})

def book_list(request):
    query = request.GET.get('q')
    if query:
        books = Book.objects.filter(title__icontains=query)
    else:
        books = Book.objects.all()
    return render(request, 'book_list.html', {'books': books}) 

@login_required(login_url='login')  
def profile(request):
    lent_books = Book.objects.filter(owner=request.user)
    received_reviews = Review.objects.filter(book__owner=request.user)
    return render(request, 'profile.html', {
        'lent_books': lent_books,
        'received_reviews': received_reviews,
    })

@login_required(login_url='login')
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = Review.objects.filter(book=book)
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()
    
    return render(request, 'book_detail.html', {
        'book': book,
        'reviews': reviews,
        'avg_rating': avg_rating
    })

@login_required(login_url='login')
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart.items.add(book)
    messages.success(request, f"Added {book.title} to your cart!")
    return redirect('book_detail', pk=pk) 

@login_required(login_url='login')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})

# --- 1. ADD TO CART ---
@login_required(login_url='login')
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    # Get or create a cart for the current user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Add the book to the cart
    cart.items.add(book)
    messages.success(request, f"Added '{book.title}' to your cart 🛒")
    
    # Go to the cart page immediately so they can see it
    return redirect('cart_view')

# --- 2. VIEW CART ---
@login_required(login_url='login')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    
    # Calculate Total Price of all items
    total_price = sum(item.price for item in items)
    
    return render(request, 'cart.html', {
        'items': items,
        'total_price': total_price
    })

# --- 3. REMOVE ITEM ---
@login_required(login_url='login')
def remove_from_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart = Cart.objects.get(user=request.user)
    cart.items.remove(book)
    messages.info(request, "Item removed from cart.")
    return redirect('cart_view')

# --- 4. CHECKOUT (UPI PAGE) ---
@login_required(login_url='login')
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    
    if not items:
        messages.error(request, "Your cart is empty!")
        return redirect('home')

    total_price = sum(item.price for item in items)

    # --- UPI CONFIGURATION ---
    # Replace with your own UPI ID if you want real payments
    upi_id = "bookbee.merchant@upi" 
    payee_name = "BookBee Store"
    
    # Create the UPI Link
    # This format tells the app to pay 'total_price' to 'upi_id'
    upi_link = f"upi://pay?pa={upi_id}&pn={payee_name}&am={total_price}&cu=INR"
    
    # Generate QR Code Image URL (using a free API)
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={upi_link}"

    return render(request, 'payment.html', {
        'total_price': total_price,
        'qr_code_url': qr_code_url,
        'upi_link': upi_link
    })

# --- 5. PAYMENT SUCCESS ---
@login_required(login_url='login')
def payment_success(request):
    cart = Cart.objects.get(user=request.user)
    cart.items.clear() # Empty the cart
    messages.success(request, "Payment Successful! Order Placed. 🐝")
    return redirect('home')

@login_required(login_url='login')
def profile(request):
    # 1. Get or Create UserProfile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # 2. Define available avatars (must match filenames in static/images/)
    available_avatars = ['av1.png', 'av2.png', 'av3.png', 'av4.png', 'av5.png']

    if request.method == 'POST':
        print("--- POST REQUEST RECEIVED ---") # Debug print 1
        
        # Check if the avatar selection data was sent
        if 'selected_avatar' in request.POST:
            avatar_filename = request.POST.get('selected_avatar')
            print(f"Selected Avatar: {avatar_filename}") # Debug print 2
            
            # 3. Update the database field
            # We save the path relative to the static folder
            new_path = f"images/{avatar_filename}"
            user_profile.avatar = new_path
            user_profile.save()
            print(f"Saved to DB: {new_path}") # Debug print 3
            
            # Force a redirect to refresh the page content
            return redirect('profile')
        else:
            print("No 'selected_avatar' found in POST data")

    # ... (rest of your context and render code) ...
    lent_books = Book.objects.filter(owner=request.user)
    received_reviews = Review.objects.filter(book__owner=request.user)

    context = {
        'user_profile': user_profile,
        'lent_books': lent_books,
        'received_reviews': received_reviews,
        'available_avatars': available_avatars,
    }
    return render(request, 'profile.html', context)