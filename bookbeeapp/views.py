from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q

from .forms import BookForm, EditProfileForm
from .models import Book, Review, Cart, UserProfile, UserCredit, Order


# 🔹 COMMON BOOK COVERS (28 BOOKS)
BOOK_COVERS = [f"books/book{i}.jpg" for i in range(1, 29)]


# ---------------- SIGNUP ----------------
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists ❌")
            return render(request, "signup.html", {"book_covers": BOOK_COVERS})

        if password1 != password2:
            messages.error(request, "Passwords do not match ❌")
            return render(request, "signup.html", {"book_covers": BOOK_COVERS})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        login(request, user)
        messages.success(request, "Account created successfully 🎉")
        return redirect("home")

    return render(request, "signup.html", {"book_covers": BOOK_COVERS})


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {
        'form': form,
        'book_covers': BOOK_COVERS
    })


# ---------------- HOME ----------------
@login_required(login_url='login')
def home(request):
    books = Book.objects.filter(status='AVAILABLE')
    return render(request, "home.html", {'books': books})


# ---------------- ADD BOOK ----------------
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


# ---------------- BOOK LIST ----------------
def book_list(request):
    query = request.GET.get('q')
    books = Book.objects.filter(title__icontains=query) if query else Book.objects.all()
    return render(request, 'book_list.html', {'books': books})


# ---------------- BOOK DETAIL ----------------
@login_required(login_url='login')
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = Review.objects.filter(book=book)
    avg_rating = sum(r.rating for r in reviews) / reviews.count() if reviews.exists() else 0

    return render(request, 'book_detail.html', {
        'book': book,
        'reviews': reviews,
        'avg_rating': avg_rating
    })


# ---------------- CART ----------------
@login_required(login_url='login')
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.add(book)
    messages.success(request, f"Added '{book.title}' to your cart 🛒")
    return redirect('cart_view')


@login_required(login_url='login')
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total_price = sum(item.price for item in items)

    return render(request, 'cart.html', {
        'items': items,
        'total_price': total_price
    })


@login_required(login_url='login')
def remove_from_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart = Cart.objects.get(user=request.user)
    cart.items.remove(book)
    messages.info(request, "Item removed from cart.")
    return redirect('cart_view')


# ---------------- CHECKOUT ----------------
@login_required(login_url='login')
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
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
    cart = Cart.objects.get(user=request.user)

    for book in cart.items.all():
        Order.objects.create(
            buyer=request.user,
            seller=book.owner,
            book=book
        )
        book.status = 'LENDED' if book.transaction_type == 'rent' else 'SOLD'
        book.save()

    cart.items.clear()
    messages.success(request, "Payment Successful! Order Placed 🐝")
    return redirect('home')


# ---------------- PROFILE ----------------
@login_required(login_url='login')
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    available_avatars = ['av1.png', 'av2.png', 'av3.png', 'av4.png', 'av5.png']

    if request.method == 'POST' and 'selected_avatar' in request.POST:
        avatar = request.POST.get('selected_avatar')
        user_profile.avatar = f"images/{avatar}"
        user_profile.save()
        return redirect('profile')

    user_credits = UserCredit.objects.filter(receiver=request.user)
    total_score = sum(c.score for c in user_credits)
    lent_books = Book.objects.filter(owner=request.user)
    borrowed_orders = Order.objects.filter(buyer=request.user)

    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'lent_books': lent_books,
        'borrowed_orders': borrowed_orders,
        'available_avatars': available_avatars,
        'user_credits': user_credits,
        'total_score': total_score
    })


# ---------------- PUBLIC PROFILE ----------------
@login_required(login_url='login')
def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    if profile_user == request.user:
        return redirect('profile')

    user_profile, _ = UserProfile.objects.get_or_create(user=profile_user)

    has_interacted = Order.objects.filter(
        (Q(buyer=request.user) & Q(seller=profile_user)) |
        (Q(buyer=profile_user) & Q(seller=request.user))
    ).exists()

    if request.method == 'POST' and has_interacted:
        message = request.POST.get('message')
        UserCredit.objects.create(
            giver=request.user,
            receiver=profile_user,
            score=1,
            message=message
        )
        messages.success(request, f"Trust Point sent to {profile_user.username}! 🛡️")

    user_credits = UserCredit.objects.filter(receiver=profile_user)
    total_score = sum(c.score for c in user_credits)
    lent_books = Book.objects.filter(owner=profile_user, status='AVAILABLE')

    return render(request, 'public_profile.html', {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'user_credits': user_credits,
        'total_score': total_score,
        'lent_books': lent_books,
        'has_interacted': has_interacted
    })


# ---------------- EDIT PROFILE ----------------
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
