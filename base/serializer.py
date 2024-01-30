from rest_framework import serializers
# from .models import UserProfile,Product,Category, Receipt
from .models import MarketUser,Product,Category, Receipt, Coupon, Contact


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketUser
        fields = ['id', 'username', 'firstname', 'lastname', 'email', 'gender', 'date_of_birth', 'img', 'is_staff']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    
class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ['id', 'products', 'price', 'user', 'discount', 'orderid']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'desc', 'percent', 'min_price']

    def create(self, validated_data):
        validated_data['code'] = Coupon.generate_unique_code()
        return super().create(validated_data)
    

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

from .models import ProductReviews

class ProductReviewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReviews
        fields = '__all__'  # Include all fields from ProductReviews model
