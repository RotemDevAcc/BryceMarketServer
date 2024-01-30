# from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import MarketUser, Product, Category, Receipt, Coupon
from .serializer import UserSerializer, ProductSerializer, CategorySerializer, ReceiptSerializer, CouponSerializer
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import SimpleUploadedFile
import json
from decimal import Decimal
from .logger import log_action
from project.settings import PAYPAL_MODE,PAYPAL_CLIENT_ID,PAYPAL_CLIENT_SECRET

from datetime import datetime, timedelta
import pytz
def check_time_elapsed(create_time_str):
    # Convert the create_time string to a datetime object
    create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))

    # Get the current UTC time
    now = datetime.now(pytz.utc)

    # Calculate the time difference
    time_diff = now - create_time

    # Check if less than 5 minutes have passed
    return time_diff < timedelta(minutes=1)


UsedOrders = []
import paypalrestsdk         
from paypalrestsdk import Sale
paypalrestsdk.configure({
    "mode": PAYPAL_MODE,  
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})

def get_sale_id(payment_id):
    try:
        # Retrieve the payment object
        payment = Sale.find(payment_id)

        if(payment):
            return {'sale_id': payment}

        return {'error': 'Sale ID not found'}
    except paypalrestsdk.ResourceNotFound:
        # Handle the exception (e.g., payment not found)
        return {'error': 'Payment not found'}
    except Exception as e:
        # Handle other exceptions
        return {'error': str(e)}

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
 
        # Add custom claims
        token['username'] = user.username
        token['firstname'] = user.firstname
        token['lastname'] = user.lastname
        token['email'] = user.email
        token['gender'] = user.gender
        token['dob'] = user.date_of_birth.isoformat() if user.date_of_birth else None
        token['img'] = str(user.img) or "placeholder.png"
        token['is_staff'] = user.is_staff or None
        return token
 
 
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

from django.http import JsonResponse

@api_view(['GET'])
def index(request):
    return JsonResponse({'message': 'No Access To This Url.'}, safe=False)





@api_view(["GET","POST"])
def productlist(request):
    if not request.method: return
    if request.method == "GET":
        try:
            products = Product.objects.all()
            serializer = ProductSerializer(products, many=True)

            categories = Category.objects.all()
            serializer2 = CategorySerializer(categories, many=True)

            combined_data = {'products': serializer.data, 'categories': serializer2.data}
            return Response(combined_data)
        except Exception as e:
            log_action("ERROR",f"Error in GET /productlist: {e}")
            return Response({"error": "An error occurred while fetching products and categories"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif request.method == "POST":
        # The Client purchased the cart
        try:
            user = request.user
            price = Decimal(str(request.data['price']))
            cart = request.data['cart']
            coupon = request.data['coupon']

            #Paypal orderid
            orderid = request.data['orderid']



            totalPrice = Decimal('0')

            PurchasedItems = []
            # Here we are looping through the items he bought
            # we make sure all the items are known to the system, and that their prices aren't messed up.
            try:
                for item_info in cart:
                    item_id = item_info.get('id')
                    product = Product.objects.get(id=item_id)
                    if product:
                        if product.price == Decimal(item_info['price']):
                            itemprice = Decimal(item_info['price'])
                            totalPrice += (itemprice * item_info['count'])
                            PurchasedItems.append({
                                "item": item_id,
                                "count": item_info['count'],
                                "price": float((itemprice * item_info['count']).quantize(Decimal('0.01')))
                            })
                        else:
                            print("Warning, Wrong Price")
                            log_action("WARNING", "Wrong Price")
                            return Response({"success": False, "message": "ERROR, Something went wrong."})
                    else:
                        print("Warning, Unauthorized Item Detected.")
                        log_action("WARNING", "Unauthorized Item Detected")
                        return Response({"success": False, "message": "ERROR, Something went wrong."})
                #if the price is as should be we carry on
                if totalPrice == price:
                    user_instance = MarketUser.objects.get(username=user)


                    # if the orderid was already used we stop the process to avoid duplications
                    if orderid in UsedOrders:
                        return Response({"success": False, "message": "This order ID has already been used."}, status=400)
                    
                    # if not we add it to UsedOrders to avoid duplications
                    UsedOrders.append(orderid)

                    # Get The Order details from paypal
                    sale_details = get_sale_id(orderid)

                    # make sure the order actually exists in paypal api
                    if(sale_details):
                        #make sure the order is not older than 1 minute.
                        if(not check_time_elapsed(sale_details['sale_id']['create_time'])):
                            return Response({"success": False, "message": "This order ID has already been used."}, status=400) # Too Old
                        
                        #if a coupon is used we caculate what price the client should pay
                        if(coupon and 'code' in coupon):
                            coupon_code = coupon['code']
                            existing_coupon = Coupon.objects.filter(code=coupon_code).first()
                            if not existing_coupon:
                                return Response({'success': False, 'message': "The Coupon You Have sent does not exist"}, status=400)
                            else:
                                print(f"Coupon {coupon_code} Found Successfully, %{coupon['percent']} Given")
                                existing_coupon.delete()
                                totalPrice = Decimal(float(totalPrice) - (coupon['percent'] / 100) * float(totalPrice))
                                totalPrice = round(totalPrice, 2)
                            
                        #Add the order to a list to avoid having it used twice
                        

                        #prepare the receipt
                        receipt_data = {
                            'orderid': orderid or "UNKNOWN ERROR",
                            'products': json.dumps(PurchasedItems),
                            'price': float(totalPrice),
                            'user': user_instance.id,
                            'discount':coupon and coupon['percent'] or 0
                        }

                        serializer = ReceiptSerializer(data=receipt_data)
                        if serializer.is_valid():
                            serializer.save()
                            log_action("INFO", "Receipt saved successfully")
                            print("Receipt saved successfully")
                            # Notify the client the purchase was completed
                            return Response({"success": True, "message": f"Purchase Complete, You Bought All The Specificed Items For ${totalPrice} {'With A Discount Of %'+ str(coupon['percent']) if coupon and coupon['percent'] > 0 else ''}"})
                        else:
                            print("Error in data:", serializer.errors)
                            log_action("ERROR", f"Error in data: {serializer.errors}")
                    else:
                        return Response({"success":False, "message":f"ERROR: OrderID {orderid or 'UNKNOWN'} does not exist."})
                else:
                    print(f"Warning Wrong Price Client Reported: {type(price)}, Server Calculated: {type(totalPrice)}")
                    print(f"Client Reported Price: {price}, Server Calculated Price: {totalPrice}")
                    return Response({"success": False, "message": "Purchase Failed"})
            except ObjectDoesNotExist:
                    print(f"Warning, Unauthorized Item Detected.")
                    log_action("WARNING", "Unauthorized Item Detected")
                    return Response({"success": False, "message": "ERROR, Something went wrong."})
        except Exception as e:
            log_action("EXCEPTION",f"Error in POST /productlist: {e}")
            return Response({"error": "An error occurred during the purchase process"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])  
@permission_classes([IsAuthenticated])
def getcoupon(request):
    data = request.data
    # make sure the coupon the client uses exists before we move on to payment
    try:

        # if no coupon was entered.
        if not data.get('coupon'):
            return Response({"success": False, "message": "Coupon not Entered"}) 
        
        # find the coupon
        coupon = Coupon.objects.get(code=data['coupon'])
        coupon_serializer = CouponSerializer(coupon)
        serialized_data = coupon_serializer.data

        # if found return its details.
        response_data = {
            "success": True,
            "message": "Coupon Entered Successfully",
            "coupon": {
                "id": serialized_data["id"],  # Adjust with the actual attribute names
                "code": serialized_data["code"],
                "percent": serialized_data["percent"],
                "min_price": serialized_data["min_price"],

                # Include other attributes as needed
            }
        }

        
        return Response(response_data) 
    #if it doesn't exist notify the client
    except Coupon.DoesNotExist:
        return Response({"success": False, "message": "Coupon not found"}) 
    except ValidationError as e:
                print(str(e)) 




@permission_classes([AllowAny])
class RegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        username = data.get('username')
        existing_user = MarketUser.objects.filter(username=username).exists()
        if existing_user:
            return Response({'success': False, 'message': "Username Already Used"}, status=400)
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        password = data.get('password')
        email = data.get('email')
        gender = data.get('gender')
        date_of_birth = data.get('date')

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({'success': False, 'message': str(e)}, status=400)

        user = MarketUser.objects.create_user(
            username=username,
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=password,
            gender=gender,
            date_of_birth=date_of_birth
        )

        return Response({'success': True, 'message': f'User: {user.username} - Registration successful'})
    


@api_view(["GET","PUT"])
@permission_classes([IsAuthenticated])
def modprofile(request):
    if request.method == "GET":
        ruser = request.user
        receipts = Receipt.objects.filter(user=ruser.id)
        serializer = ReceiptSerializer(receipts, many=True)
        
        return Response({"success": True, 'message': "Receipts Received", 'receipts': serializer.data})
        

    elif request.method == "PUT":
        ruser = request.user
        rtype = request.data.get('rtype')

        if rtype == "newpicture":
            try:
                user = MarketUser.objects.get(id=ruser.id)
                if ruser.id != user.id:
                    return Response({"success":False,'message':"Something Went Wrong(1)"})
                
                image_file = request.data.get('img')
                    
                if image_file:
                    # Check file format and size
                    allowed_formats = ['.png']
                    max_size = 2 * 1024 * 1024  # 2MB
                        
                    if not image_file.name.lower().endswith(tuple(allowed_formats)):
                        raise ValidationError("Please upload a PNG image.")
                        
                    if image_file.size > max_size:
                        raise ValidationError("Image size must be less than 2MB.")
                    
                    # Use the serializer to update the user instance
                    data = {'img': SimpleUploadedFile(image_file.name, image_file.read(), content_type='image/png')}
                    serializer = UserSerializer(user, data=data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response({"success": True, 'message': "Picture Changed Successfully", 'picname':image_file.name or None})
                    else:
                        return Response({"success": False, 'message': "Something Went Wrong"})
                        
                
                return Response({"success":False,'message':"Image Was Not Found."})
            except MarketUser.DoesNotExist:
                return Response({'success': True, 'message': f'Something Went Wrong'})
            except ValidationError as e:
                print(str(e))
                return Response({'success': False, 'message': "Something Went Wrong"}, status=400)
        elif rtype == "newname":
            try:
                user = MarketUser.objects.get(id=ruser.id)
                if ruser.id != user.id:
                    return Response({"success":False,'message':"Something Went Wrong(1)"})
                
                firstname = request.data.get('firstname')
                lastname = request.data.get('lastname')
                    
                if firstname and lastname:

                    if user.firstname == firstname and user.lastname == lastname:
                        return Response({"success": False, 'message':"Your New Name cant be the same as your current name."})
                    # Check file format and size

                    # Use the serializer to update the user instance
                    data = {'firstname':firstname,'lastname':lastname}
                    serializer = UserSerializer(user, data=data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response({"success": True, 'message': f"Name Changed Successfully To {firstname} {lastname}","firstname":firstname,"lastname":lastname})
                    else:
                        return Response({"success": False, 'message': "Something Went Wrong"})
                        
                return Response({"success":False,'message':"Firstname or Lastname weren't specified"})
            except MarketUser.DoesNotExist:
                return Response({'success': True, 'message': f'Something Went Wrong'})
            except ValidationError as e:
                print(str(e))
                return Response({'success': False, 'message': "Something Went Wrong"}, status=400)
        else:
            return Response({"success":False,'message':"Something Went Wrong"})

