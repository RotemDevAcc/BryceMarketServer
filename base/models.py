from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

def validate_alpha(value):
    if not value.isalpha():
        raise ValidationError("Only letters are allowed in the first name.")

class MarketUser(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    firstname = models.CharField(max_length=50, null=True, validators=[validate_alpha])
    lastname = models.CharField(max_length=50,null=True, validators=[validate_alpha])
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    img = models.ImageField(null=True,blank=True,default='/placeholder.png')

    def __str__(self):
        return self.username
    
class Receipt(models.Model):
    id = models.AutoField(primary_key=True)
    orderid = models.CharField(max_length=50,null=True)
    products = models.TextField()
    price = models.FloatField(null=True)
    user = models.ForeignKey(MarketUser, on_delete=models.CASCADE, null=True)  # Foreign key to User
    discount = models.FloatField(null=True,default=0)

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    desc = models.CharField(max_length=80,null=True)
    def __str__(self):
           return self.desc
    
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50,null=True)
    desc = models.CharField(max_length=80,null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    img = models.ImageField(null=True,blank=True,default='/placeholder.png')
    createdTime=models.DateTimeField(auto_now_add=True,null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True)  # Foreign key to Category
 
    def __str__(self):
           return self.desc
    
import uuid
from django.db import models

class Coupon(models.Model):
    id = models.AutoField(primary_key=True) 
    code = models.CharField(max_length=150, null=True, unique=True)
    desc = models.CharField(max_length=80, null=True)
    percent = models.FloatField(null=True)
    min_price = models.FloatField(default=100, null=True)

    @staticmethod
    def generate_unique_code():
        return str(uuid.uuid4())[:8]  # Generates a unique 8 character code
