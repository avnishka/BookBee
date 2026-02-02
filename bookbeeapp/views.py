from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm 
from .forms import BookForm, EditProfileForm 
from .models import Book, Review, Cart, UserProfile, UserCredit, Order
from django.db.models import Q  
from chat.models import ChatRoom
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# --- HOME VIEW ---
def home(request):
    books = Book.objects.all().order_by('-created_at')

    query = request.GET.get('q')

    if query:
        # Filter by Title OR Genre OR Location (Case insensitive)
        books = books.filter(
            Q(title__icontains=query) | 
            Q(genre__icontains=query) | 
            Q(location__icontains=query)
        )

    return render(request, 'home.html', {'books': books})

# --- AUTH VIEWS ---
def signup_view(request):
    BOOK_COVERS = [f"books/book{i}.jpg" for i in range(1, 29)]

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not password:
            messages.error(request, "Username and Password are required.")
            return render(request, "signup.html", {"book_covers": BOOK_COVERS})

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "signup.html", {"book_covers": BOOK_COVERS})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, "signup.html", {"book_covers": BOOK_COVERS})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, "signup.html", {"book_covers": BOOK_COVERS})

        # Create User
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False 
        user.save()

        # ✅ FIX: Create UserProfile immediately to prevent "User has no userprofile" error
        UserProfile.objects.create(user=user)

        # Send Email
        domain = request.get_host()
        mail_subject = 'Activate your BookBee account 🐝'
        message = render_to_string('acc_active_email.html', {
            'user': user,
            'domain': domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        
        try:
            email_msg = EmailMessage(mail_subject, message, to=[email])
            email_msg.send()
            messages.success(request, "Please check your email to verify your account! 📧")
        except Exception as e:
            messages.error(request, f"Error sending email: {e}")

        return redirect("login_view")
        
    return render(request, "signup.html", {"book_covers": BOOK_COVERS})

def login_view(request):
    BOOK_COVERS = [f"books/book{i}.jpg" for i in range(1, 29)]
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
    return render(request, 'login.html', {'form': form, 'book_covers': BOOK_COVERS})

# --- BOOK ACTIONS ---
@login_required(login_url='login_view') 
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

@login_required(login_url='login_view')
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    has_bought = Order.objects.filter(buyer=request.user, book=book).exists()

    if request.method == 'POST' and 'submit_review' in request.POST:
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

    reviews = Review.objects.filter(book=book).order_by('-id')
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    return render(request, 'book_detail.html', {
        'book': book,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'has_bought': has_bought
    })

# --- CART & CHECKOUT ---
@login_required(login_url='login_view')
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    
    # 1. ✅ FIX: Loophole Closed - Check ownership FIRST
    if book.owner == request.user:
        messages.error(request, "You cannot borrow or buy your own book! 🐝")
        return redirect('home')

    # 2. Add to Cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart.items.add(book)

    # 3. Create Chat Room
    ChatRoom.objects.get_or_create(user1=request.user, user2=book.owner)
    
    messages.success(request, f"Added {book.title} to your cart!")
    return redirect('cart_view')

@login_required(login_url='login_view')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = []
    for book in cart.items.all():
        room, created = ChatRoom.objects.get_or_create(user1=request.user, user2=book.owner)
        book.room = room
        items.append(book)

    total_price = sum(book.price for book in items)
    return render(request, 'cart.html', {'items': items, 'total_price': total_price})

@login_required(login_url='login_view')
def remove_from_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart = Cart.objects.get(user=request.user)
    cart.items.remove(book)
    messages.info(request, "Item removed from cart.")
    return redirect('cart_view')

@login_required(login_url='login_view')
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

@login_required(login_url='login_view')
def payment_success(request):
    cart = Cart.objects.get(user=request.user)
    
    for book in cart.items.all():
        Order.objects.create(buyer=request.user, seller=book.owner, book=book)
        
        if book.transaction_type == 'rent':
            book.status = 'LENDED'
            book.is_available = False  
        else:
            book.owner = request.user 
            book.status = 'SOLD'       
            book.is_available = False  
        book.save()

    cart.items.clear()
    messages.success(request, "Payment Successful! Order Placed. 🐝")
    return redirect('home')

# --- PROFILE VIEWS ---
@login_required(login_url='login_view')
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # ✅ HANDLE AVATAR UPDATE
    if request.method == "POST" and request.POST.get("selected_avatar"):
        selected_avatar = request.POST.get("selected_avatar")
        user_profile.avatar = selected_avatar
        user_profile.save()
        messages.success(request, "Avatar updated successfully! 🐝")
        return redirect('profile')

    # 1. ✅ TRUST SCORE LOGIC
    if request.method == 'POST' and request.POST.get('action') == 'give_credit':
        target_username = request.POST.get('target_username')
        message = request.POST.get('message', 'Verified transaction trust point.')
        target_user = get_object_or_404(User, username=target_username)
        
        if target_user == request.user:
            messages.error(request, "You cannot increase your own trust score! 🚫")
            return redirect('profile')

        has_transacted = Order.objects.filter(
            (Q(buyer=request.user) & Q(seller=target_user)) | 
            (Q(buyer=target_user) & Q(seller=request.user))
        ).exists()

        if has_transacted:
            if not UserCredit.objects.filter(giver=request.user, receiver=target_user).exists():
                UserCredit.objects.create(giver=request.user, receiver=target_user, score=1, message=message)
                messages.success(request, f"Trust score for @{target_username} increased! 🛡️")
            else:
                messages.warning(request, "You have already given trust points to this user.")
        else:
            messages.error(request, "You can only give trust points to users you have traded with! 🚫")
        return redirect('profile')

    # --- PAGE DATA ---
    user_credits = UserCredit.objects.filter(receiver=request.user).order_by('-created_at')
    total_score = sum(c.score for c in user_credits)
    my_listings = Book.objects.filter(owner=request.user).exclude(status='SOLD').order_by('-created_at')
    borrowed_books = Order.objects.filter(buyer=request.user, book__transaction_type='rent').order_by('-created_at')
    purchased_books = Order.objects.filter(buyer=request.user, book__transaction_type='buy').order_by('-created_at')

    context = {
        'user_profile': user_profile,
        'my_listings': my_listings,
        'borrowed_books': borrowed_books,
        'purchased_books': purchased_books,
        'available_avatars': ['av1.png', 'av2.png', 'av3.png', 'av4.png', 'av5.png'],
        'total_score': total_score,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='login_view')
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

@login_required(login_url='login_view')
def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    # 🔁 Redirect if trying to view own public profile
    if profile_user == request.user:
        return redirect('profile')

    user_profile = get_object_or_404(UserProfile, user=profile_user)

    has_interacted = Order.objects.filter(
        (Q(buyer=request.user) & Q(seller=profile_user)) | 
        (Q(buyer=profile_user) & Q(seller=request.user))
    ).exists()

    # 🛡️ Handle Trust Point
    if request.method == 'POST' and request.POST.get('give_credit'):
        if has_interacted:
            message = request.POST.get('message', 'Verified transaction trust point.')

            if not UserCredit.objects.filter(giver=request.user, receiver=profile_user).exists():
                UserCredit.objects.create(
                    giver=request.user,
                    receiver=profile_user,
                    score=1,
                    message=message
                )
                messages.success(request, f"Trust Point sent to @{profile_user.username}! 🛡️")
            else:
                messages.warning(request, "You already gave a trust point to this user.")
        else:
            messages.error(request, "You must transact with this user first.")
        return redirect('public_profile', username=username)

    # 📊 Trust Score
    user_credits = UserCredit.objects.filter(receiver=profile_user).order_by('-created_at')
    total_score = sum(c.score for c in user_credits)

    # 📚 Active Listings
    lent_books = Book.objects.filter(owner=profile_user).exclude(status='SOLD')

    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'user_credits': user_credits,
        'total_score': total_score,
        'lent_books': lent_books,
        'has_interacted': has_interacted,
    }

    return render(request, 'public_profile.html', context)


@login_required(login_url='login_view')
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.user != book.owner:
        messages.error(request, "You are not authorized to delete this book.")
        return redirect('profile')
    if book.status != 'AVAILABLE':
        messages.error(request, "Cannot delete this book because it is currently rented or sold.")
        return redirect('profile')
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Book removed from listings successfully. 🗑️")
    return redirect('profile')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account is activated! You can now log in. 🐝')
        return redirect('login_view')
    else:
        messages.error(request, 'Activation link is invalid or expired!')
        return redirect('signup_view')