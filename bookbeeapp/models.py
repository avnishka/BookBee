from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    STATUS_CHOICES = [('AVAILABLE', 'Available'), ('LENDED', 'Lended'), ('SOLD', 'Sold')]
    TRANSACTION_CHOICES = [('rent', 'For Rent'), ('buy', 'For Sale')]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='book_covers/')
    price = models.DecimalField(max_digits=6, decimal_places=2, help_text="Rent per day or Sale price")
    security_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, blank=True, null=True)
    location = models.CharField(max_length=150)
    
    # --- THIS WAS MISSING ---
    description = models.TextField(blank=True, null=True) 
    # ------------------------

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES, default='rent')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Book)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.CharField(max_length=255, default='images/default.png') 

    def __str__(self):
        return self.user.username