from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm 
from .forms import BookForm, EditProfileForm 
from .models import Book, Review, Cart, UserProfile, UserCredit, Order
from django.db.models import Q  

# --- HOME VIEW (Merged Logic) ---
def home(request):
    # 1. Start with Available books
    books = Book.objects.filter(status='AVAILABLE').order_by('-created_at')

    # 2. Get Filters
    query = request.GET.get('q')
    location = request.GET.get('location')
    genre = request.GET.get('genre')
    sort_option = request.GET.get('sort')

    # 3. Apply Search 
    # (Removed 'author' to fix the crash. Added 'genre' so text search works better)
    if query:
        books = books.filter(
            Q(title__icontains=query) | 
            Q(pincode__icontains=query) | 
            Q(location__icontains=query) |
            Q(genre__icontains=query)
        )

    # 4. Apply Dropdown Filters
    if location:
        books = books.filter(location__icontains=location)
    
    if genre:
        books = books.filter(genre__iexact=genre)

    # 5. Sorting
    if sort_option == 'low_to_high':
        books = books.order_by('price')
    elif sort_option == 'high_to_low':
        books = books.order_by('-price')

    return render(request, 'home.html', {'books': books})

# --- AUTH VIEWS ---
def signup_view(request):
    if request.method == "POST":
        # 1. Get data and STRIP whitespace
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # 2. Validations
        if not username or not password:
            messages.error(request, "Username and Password are required.")
            return redirect("signup")
            
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("signup")

        # 3. Create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # --- CHANGES START HERE ---
        
        # REMOVED: login(request, user, backend='...') 
        # We do NOT log them in automatically anymore.
        
        # 4. Redirect to LOGIN page with a success message
        messages.success(request, "Account created successfully! Please log in. 🐝")
        return redirect("login") 
        
        # --- CHANGES END HERE ---
        
    return render(request, "signup.html")

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # authenticate() checks the hashed password
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            # This triggers if password doesn't match hash
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'login.html', {'form': form})

# --- BOOK ACTIONS ---
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
    # Simple list view
    query = request.GET.get('q')
    if query:
        books = Book.objects.filter(title__icontains=query)
    else:
        books = Book.objects.all()
    return render(request, 'book_list.html', {'books': books}) 

@login_required(login_url='login')
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # 1. VERIFICATION: Check if the user has actually ordered this book
    # We look for an Order where the 'buyer' is the current user and 'book' is this book
    has_bought = Order.objects.filter(buyer=request.user, book=book).exists()

    # 2. Handle Review Submission (POST Request)
    if request.method == 'POST' and 'submit_review' in request.POST:
        # Security Check: Prevent forced reviews via inspecting element
        if not has_bought:
            messages.error(request, "You must borrow or buy this book to review it! 🚫")
            return redirect('book_detail', pk=pk)

        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            Review.objects.create(
                author=request.user,
                book=book,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Review added successfully! ⭐")
            return redirect('book_detail', pk=pk)

    # 3. Get existing reviews
    reviews = Review.objects.filter(book=book).order_by('-id')
    
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    # Pass 'has_bought' to the template so we can hide/show the form
    return render(request, 'book_detail.html', {
        'book': book,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'has_bought': has_bought
    })

# --- CART & CHECKOUT ---
@login_required(login_url='login')
def add_to_cart(request, pk):

    book = get_object_or_404(Book, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Standard Logic: Add the new book to existing items
    cart.items.add(book)
    
    messages.success(request, f"Added {book.title} to your cart!")
    return redirect('cart_view')

@login_required(login_url='login')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total_price = sum(item.price for item in items)
    return render(request, 'cart.html', {'items': items, 'total_price': total_price})

@login_required(login_url='login')
def remove_from_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart = Cart.objects.get(user=request.user)
    cart.items.remove(book)
    messages.info(request, "Item removed from cart.")
    return redirect('cart_view')

@login_required(login_url='login')
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    
    if not items:
        messages.error(request, "Your cart is empty!")
        return redirect('home')

    total_price = sum(item.price for item in items)
    upi_id = "bookbee.merchant@upi" 
    payee_name = "BookBee Store"
    upi_link = f"upi://pay?pa={upi_id}&pn={payee_name}&am={total_price}&cu=INR"
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={upi_link}"

    return render(request, 'payment.html', {
        'total_price': total_price,
        'qr_code_url': qr_code_url,
        'upi_link': upi_link
    })

@login_required(login_url='login')
def payment_success(request):
    # 1. Get the user's cart
    cart = Cart.objects.get(user=request.user)
    
    # 2. Process each book
    for book in cart.items.all():
        # A. Create the Order Record (Proof of purchase/rent)
        # IMPORTANT: We do this BEFORE changing ownership so we record the correct seller.
        Order.objects.create(
            buyer=request.user,
            seller=book.owner, 
            book=book
        )
        
        # B. RENT vs BUY Logic
        if book.transaction_type == 'rent':
            # --- SCENARIO 1: RENT ---
            # ERROR FIX: Do NOT change book.owner
            # The owner stays as the original lender (e.g., Abhya)
            book.status = 'LENDED'
            book.is_available = False  
            
        else:
            # --- SCENARIO 2: BUY ---
            # Ownership transfers to YOU (Buyer)
            book.owner = request.user 
            book.status = 'SOLD'       
            book.is_available = False  

        # C. Save the changes to the database
        book.save()

    # 3. Clear cart and finish
    cart.items.clear()
    messages.success(request, "Payment Successful! Order Placed. 🐝")
    return redirect('home')

# --- PROFILE VIEWS ---
@login_required(login_url='login')
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    available_avatars = ['av1.png', 'av2.png', 'av3.png', 'av4.png', 'av5.png']

    # Handle Avatar Change
    if request.method == 'POST':
        if 'selected_avatar' in request.POST:
            avatar_filename = request.POST.get('selected_avatar')
            user_profile.avatar = f"images/{avatar_filename}"
            user_profile.save()
            return redirect('profile')

    user_credits = UserCredit.objects.filter(receiver=request.user).order_by('-created_at')
    total_score = sum(c.score for c in user_credits)
    
    # --- TAB 1: LENDING (My Listings) ---
    # Books I own that are Available or currently Lent out.
    # We EXCLUDE 'SOLD' because those are books I bought for myself.
    my_listings = Book.objects.filter(owner=request.user).exclude(status='SOLD').order_by('-created_at')
    
    # --- TAB 2: BORROWED (Rentals) ---
    # Orders where I am the buyer AND the book was for 'rent'
    borrowed_books = Order.objects.filter(buyer=request.user, book__transaction_type='rent').order_by('-created_at')
    
    # --- TAB 3: HISTORY (Purchases) ---
    # Orders where I am the buyer AND the book was for 'buy'
    purchased_books = Order.objects.filter(buyer=request.user, book__transaction_type='buy').order_by('-created_at')

    context = {
        'user_profile': user_profile,
        'my_listings': my_listings,       # Tab 1
        'borrowed_books': borrowed_books, # Tab 2
        'purchased_books': purchased_books, # Tab 3
        'available_avatars': available_avatars,
        'user_credits': user_credits,
        'total_score': total_score,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully ✨")
            return redirect('profile')
        return render(request, 'edit_profile.html', {'form': form})

    form = EditProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

@login_required(login_url='login')
def public_profile(request, username):

    profile_user = get_object_or_404(User, username=username)
    
    if profile_user == request.user:
        return redirect('profile')

    user_profile, created = UserProfile.objects.get_or_create(user=profile_user)

    has_interacted = Order.objects.filter(
        (Q(buyer=request.user) & Q(seller=profile_user)) | 
        (Q(buyer=profile_user) & Q(seller=request.user))
    ).exists()

    if request.method == 'POST':
        if has_interacted:
            message = request.POST.get('message')
            UserCredit.objects.create(
                giver=request.user,
                receiver=profile_user,
                score=1,
                message=message
            )
            messages.success(request, f"Trust Point sent to {profile_user.username}! 🛡️")
        else:
            messages.error(request, "You must transact with this user first.")
        return redirect('public_profile', username=username)

    user_credits = UserCredit.objects.filter(receiver=profile_user).order_by('-created_at')
    total_score = sum(c.score for c in user_credits)
    lent_books = Book.objects.filter(owner=profile_user, status='AVAILABLE')

    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'user_credits': user_credits,
        'total_score': total_score,
        'lent_books': lent_books,
        'has_interacted': has_interacted,
    }
    return render(request, 'public_profile.html', context)

@login_required(login_url='login')
def book_detail(request, pk):

    book = get_object_or_404(Book, pk=pk)
    
    # 1. VERIFICATION CHECK: Has this user bought/rented this book?
    # We look for an Order record where buyer is the current user and book is this book.
    has_bought = Order.objects.filter(buyer=request.user, book=book).exists()

    # 2. Handle Review Submission (Only if verified)
    if request.method == 'POST' and 'submit_review' in request.POST:
        # Security Check: Even if they inspect element to show the form, backend blocks it.
        if not has_bought:
            messages.error(request, "You must borrow or buy this book to review it! 🚫")
            return redirect('book_detail', pk=pk)

        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            Review.objects.create(
                author=request.user,
                book=book,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Review added successfully! ⭐")
            return redirect('book_detail', pk=pk)

    # 3. Get existing reviews & Calculate Average
    reviews = Review.objects.filter(book=book).order_by('-id')
    
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    return render(request, 'book_detail.html', {
        'book': book,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'has_bought': has_bought  # <--- Passing this permission flag to the template
    })

@login_required(login_url='login')
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # 1. Security Check: Are you the owner?
    if request.user != book.owner:
        messages.error(request, "You are not authorized to delete this book.")
        return redirect('profile')

    # 2. Status Check: Can only delete 'Available' books
    if book.status != 'AVAILABLE':
        messages.error(request, "Cannot delete this book because it is currently rented or sold.")
        return redirect('profile')

    # 3. Perform Deletion
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Book removed from listings successfully. 🗑️")
    
    return redirect('profile')