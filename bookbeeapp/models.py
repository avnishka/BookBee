import re
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
    pincode = models.CharField(max_length=6, blank=True)
    is_available = models.BooleanField(default=True)
    
    # --- THIS WAS MISSING ---
    description = models.TextField(blank=True, null=True) 
    # ------------------------

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES, default='rent')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        match = re.search(r'\b\d{6}\b', self.location)
        if match:
            self.pincode = match.group()
        super().save(*args, **kwargs)


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
    
class UserCredit(models.Model):
    giver = models.ForeignKey(User, related_name='credits_given', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='credits_received', on_delete=models.CASCADE)
    score = models.IntegerField(default=1) # e.g., +1 for a good interaction
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.giver.username} -> {self.receiver.username}"
    
class Order(models.Model):
    buyer = models.ForeignKey(User, related_name='purchases', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, related_name='sales', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} bought {self.book.title} from {self.seller.username}"