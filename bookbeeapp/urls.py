from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("", views.home, name="home"),
    path("login_view/", views.login_view, name="login_view"),
    path("signup_view/", views.signup_view, name="signup_view"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('books/', views.book_list, name='book_list'),
    path('add-book/', views.add_book, name='add_book'),
    path('profile/', views.profile, name = 'profile'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('chat/', include('chat.urls')),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    path('delete-book/<int:pk>/', views.delete_book, name='delete_book'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

