from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage

from .models import MarketUser, Product, Receipt, Category, Coupon
from .serializer import UserSerializer, ProductSerializer, CategorySerializer, ReceiptSerializer, CouponSerializer

import json
from .logger import log_action
# Management
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def receipts(request):    
    try:
        receipts = Receipt.objects.all()
        products = Product.objects.all()
        product_serializer = ProductSerializer(products, many=True)  
        allproducts = product_serializer.data  
        payload = []
        for receipt in receipts:
            try:
                recuser = MarketUser.objects.get(id=receipt.user_id)
                products_list = json.loads(receipt.products)
                payload.append({
                    "id": receipt.id,
                    "orderid": receipt.orderid,
                    "price": receipt.price,
                    "products": products_list,
                    "discount": receipt.discount,
                    "recuser": {"userid": recuser.id, "username": recuser.username}
                })
            except MarketUser.DoesNotExist as e:
                log_action("ERROR",f"User Receipts not found: {e}")
                return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success":True,"payload":payload,"products":allproducts,"message":"Success"})
    except Exception as e:
        log_action("ERROR",f"Error in retrieving receipts: {e}")
        return Response({"error": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_user_receipts(request,pk):
    try:
        ruser = MarketUser.objects.get(id=pk)

        # If no search criteria provided, get all receipts for the user
        receipts = Receipt.objects.filter(user=ruser.id)
        serializer = ReceiptSerializer(receipts, many=True)
        products = Product.objects.all()
        pserializer = ProductSerializer(products, many=True)
                
        categories = Category.objects.all()
        cserializer = CategorySerializer(categories, many=True)

            # Combine the serialized data into a single dictionary
        combined_data = {
            'products': pserializer.data,
            'categories': cserializer.data,
        }
        
            
        return Response({"success": True, 'message': "Receipts Received", 'receipts': serializer.data, 'combdata':combined_data})
    except MarketUser.DoesNotExist:
        return Response({"success": False, "message": f"User {pk} not found"})
    

lockdown = False

@api_view(["PUT"])
@permission_classes([IsAuthenticated,IsAdminUser])
def setstaff(request):
    if lockdown:
        return Response({"success": False, "message": f"User not found"})
    
    try:
        data = json.loads(request.body)
        user = request.user
        if(not user.is_superuser):
            if user.is_staff:
                return Response({"success": False, "message": f"You have no access to this command."})
            else:
                 return Response({"success": False, "message": f"Something Went Wrong"})
        targetuser = data.get('userid')
        ruser = MarketUser.objects.get(id=targetuser)
        setadmin = data.get('set')
        setdata = {'is_staff':setadmin}
        serializer = UserSerializer(ruser, data=setdata, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, 'customer':serializer.data,'message': f"{ruser.username} Was {'Promoted To Staff' if setadmin else 'Demoted From Staff'} Refresh the page to update."})
        else:
            return Response({"success": False, 'message': "Something Went Wrong(2)"})
    except MarketUser.DoesNotExist:
        return Response({"success": False, "message": f"User  not found"})
    

# def get_user_receipts(request,pk):
    # try:
        # ruser = MarketUser.objects.get(id=pk)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated,IsAdminUser])
def deleteuser(request,pk):
    if lockdown:
        return Response({"success": False, "message": f"User not found"})
    
    try:
        # data = json.loads(request.body)
        user = request.user
        if(not user.is_superuser):
            if user.is_staff:
                return Response({"success": False, "message": f"You have no access to this command."})
            else:
                 return Response({"success": False, "message": f"Something Went Wrong"})
        targetuser = pk
        ruser = MarketUser.objects.get(id=pk)
        serializer = UserSerializer(ruser)


        userdata = serializer.data
        userdata['id'] = pk

        savename = ruser
        ruser.delete()
        return Response({"success": True, 'customer':userdata ,'message': f"{savename} - {targetuser} Was Deleted Refresh the page to update."})

    except MarketUser.DoesNotExist:
        return Response({"success": False, "message": f"User  not found"})



@permission_classes([IsAuthenticated, IsAdminUser])
class UManagementView(APIView):
    def get(self, request):
        try:
            users = MarketUser.objects.all()
            sendusers = []
            for user in users:
                sendusers.append({
                    "username": user.username,
                    "id": user.id,
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                    "email": user.email,
                    "gender": user.gender,
                    "dob": user.date_of_birth.isoformat() if user.date_of_birth else None,
                    "img": user.img,
                    "is_staff": user.is_staff,
                })        
            serializer = UserSerializer(sendusers, many=True)
            return Response(serializer.data)
        except Exception as e:
            log_action("ERROR",f"Error in GET /umanagment/users: {e}")
            return Response({"error": "An error occurred while fetching users"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data, context={'user': request.user})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_action("ERROR",f"Error in POST /umanagment/users: {e}")
            return Response({"error": "An error occurred while creating a user"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
    def put(self, request, pk):
        try:
            user = MarketUser.objects.get(pk=pk)
            serializer = UserSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MarketUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_action("ERROR",f"Error in PUT /users/{pk}: {e}")
            return Response({"error": "An error occurred while updating the user"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    def delete(self, request, pk):
        try:
            user = MarketUser.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MarketUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_action("ERROR",f"Error in DELETE /users/{pk}: {e}")
            return Response({"error": "An error occurred while deleting the user"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@permission_classes([IsAuthenticated, IsAdminUser])
class CManagementView(APIView):
    def get(self, request):
        try:
            coupons = Coupon.objects.all()   
            serializer = CouponSerializer(coupons, many=True)
            return Response(serializer.data)
        except Exception as e:
            log_action("ERROR",f"Error in GET /coupons/: {e}")
            return Response({"error": "An error occurred while trying to get all coupons"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = CouponSerializer(data=request.data, context={'user': request.user})
            if serializer.is_valid():
                serializer.save()
                code = serializer.data['code'] or "UNKNOWN ERROR"
                return Response({"success": True, "message": f"Coupon Added Successfully - Code: {code}", "returncode":code}, status=status.HTTP_201_CREATED)
            return Response({"success": False, "message": "Coupon Creation Failed"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_action("ERROR",f"Error in POST /coupons: {e}")
            return Response({"success": False,"error": "An error occurred while creating a coupon"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    def put(self, request, pk):
        try:
            coupon = Coupon.objects.get(pk=pk)
            serializer = CouponSerializer(coupon, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({"error": "Coupon not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_action("ERROR",f"Error in PUT /coupons/{pk}: {e}")
            return Response({"error": "An error occurred while updating the coupon"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    def delete(self, request, pk):
        try:
            coupon = Coupon.objects.get(pk=pk)
            coupon.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Coupon.DoesNotExist:
            return Response({"error": "Coupon not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_action("ERROR",f"Error in DELETE /coupons/{pk}: {e}")
            return Response({"error": "An error occurred while deleting the coupon"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated, IsAdminUser])
class ProductsView(APIView):
    """
    This class handle the CRUD operations for MyModel
    """
    def get(self, request):
        try:
            products = Product.objects.all()
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Exception as e:
            log_action("ERROR",f"Error in GET /products: {e}")
            return Response({"error": "An error occurred while fetching products"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        try:
            serializer = ProductSerializer(data=request.data, context={'user': request.user})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_action("ERROR",f"Error in POST /products: {e}")
            return Response({"error": "An error occurred while creating a product"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    def put(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_action("ERROR",f"Error in PUT /products/{pk}: {e}")
            return Response({"error": "An error occurred while updating the product"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_action("ERROR",f"Error in DELETE /products/{pk}: {e}")
            return Response({"error": "An error occurred while deleting the product"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@permission_classes([IsAuthenticated, IsAdminUser])
class PManagemetView(APIView):
    """
    This class handle the CRUD operations for MyModel
    """
    def get(self, request):
        """
        Handle GET requests to return a list of MyModel objects
        """
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)

        categories = Category.objects.all()
        serializer2 = CategorySerializer(categories, many=True)

        merged_data = {
            "products": serializer.data,
            "categories": serializer2.data,
        }

        return Response(merged_data)


    def post(self, request):
        """
        Handle POST requests to create a new Task object
        """
        reqtype = request.data.get('type')
        if not reqtype or reqtype == None:
            return Response({"success": False, "message": f"Request Failed"}, status=status.HTTP_400_BAD_REQUEST)
        
        if reqtype == "product":
            
            serializer = ProductSerializer(data=request.data, context={'user': request.user})
            if serializer.is_valid():
                image_file = request.data.get('img')
                
                if image_file:
                    # Check file format and size
                    allowed_formats = ['.png']
                    max_size = 2 * 1024 * 1024  # 2MB
                    
                    if not image_file.name.lower().endswith(tuple(allowed_formats)):
                        raise ValidationError("Please upload a PNG image.")
                    
                    if image_file.size > max_size:
                        raise ValidationError("Image size must be less than 2MB.")
                    
                    request.data['img'] = SimpleUploadedFile(image_file.name, image_file.read())
                    
                serializer.save()
                return Response({"success": True, "message": f"The Product Was Added Successfully", "product":serializer.data},status=status.HTTP_201_CREATED)
            return Response({"success": False, "message": f"The Product couldn't be added"}, status=status.HTTP_400_BAD_REQUEST)
        elif reqtype == "category":
            serializer = CategorySerializer(data=request.data, context={'user': request.user})
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": f"The Category Was Added Successfully", "category":serializer.data},status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif reqtype == "delcategory":

            data = request.data
            try:
                category_id = int(data['categoryid'])
                category = Category.objects.get(pk=category_id)
            except (ValueError, Category.DoesNotExist):
                # Handle the case where categoryid is not a valid integer or category does not exist
                return Response({"success": False, "message": "Invalid category ID or Category not found."}, status=status.HTTP_400_BAD_REQUEST)

            products = Product.objects.filter(category=category)
            if products.exists():
                return Response({"success": False, "message": "There are some products that are using this category, remove them first."}, status=status.HTTP_400_BAD_REQUEST)

            # Proceed with category removal
            # ...
            category.delete()
            return Response({"success": True, "message": "The Category Was Removed Successfully", "category": category_id}, status=status.HTTP_201_CREATED)
    def put(self, request, pk):
        """
        Handle PUT requests to update an existing product
        """
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                # Handle the uploaded image file
                image_file = request.data.get('image')
                
                if image_file:
                    # Check file format and size
                    allowed_formats = ['.png']
                    max_size = 2 * 1024 * 1024  # 2MB
                    
                    if not image_file.name.lower().endswith(tuple(allowed_formats)):
                        raise ValidationError("Please upload a PNG image.")
                    
                    if image_file.size > max_size:
                        raise ValidationError("Image size must be less than 2MB.")
                    
                    product.img = SimpleUploadedFile(image_file.name, image_file.read())

                serializer.save()
                # return Response(serializer.data)
                return Response({"success":True,"message":f"Product {product.name} Has been updated successfully", "product":serializer.data})
        except Product.DoesNotExist:
            return Response({"success": False, "message": f"Product {pk} not found"})
    
        return Response({"success":False,"message":"The Product was not found."})
   
    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            
            # Check if the product's image is not the default placeholder
            if product.img.name != '/placeholder.png':
                # Delete the image file from storage
                default_storage.delete(product.img.name)

            product.delete()
            return Response({"success": True, "message": f"Product {pk} Was Deleted Successfully","product":pk})
        except Product.DoesNotExist:
            return Response({"success": False, "message": f"Product {pk} not found"})
        
#end management
