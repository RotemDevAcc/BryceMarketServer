from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Receipt, ProductReviews
from .serializer import ProductReviewsSerializer  # You'll need to create this serializer
import json
from .logger import log_action

class CreateProductReview(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this view


    def get(self, request, pk, *args, **kwargs):
        try:
            # Retrieve all reviews for the specified productid
            reviews = ProductReviews.objects.filter(product=pk)
            serializer = ProductReviewsSerializer(reviews, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            # Log the exception
            log_action("EXCEPTION","An error occurred while retrieving reviews.")
            # Optionally, you can also log the actual exception message
            # log_action("EXCEPTION",f"An error occurred while retrieving reviews: {e}")

            # Return a generic error response
            return Response("An unexpected error occurred.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:

            user = request.user
            email = user.email
            name = f"{user.firstname} {user.lastname}"
            message = request.data.get('message', '')
            product = request.data.get('productid')
            if(not product):
                return Response({"success":False,"message":"No Reviewed Product Found."},
                                status=status.HTTP_400_BAD_REQUEST)
            

            product = int(product)
            
            if not message or len(message) < 10:
                return Response({"success":False,"message":"Message is too short (minimum 10 characters)"},
                                status=status.HTTP_400_BAD_REQUEST)
            elif len(message) > 200:
                return Response({"success":False,"message":"Message is too long (maximum 200 characters)"},
                            status=status.HTTP_400_BAD_REQUEST)
            

            user_receipts = Receipt.objects.filter(user=user)
            has_bought_product = any(
                product == item.get('item') for receipt in user_receipts
                for item in json.loads(receipt.products)
            )

            if not has_bought_product:
                return Response({"success": False, "message": "You can't review a product you haven't bought yet."},
                                status=status.HTTP_403_FORBIDDEN)

            data = {'product':product,'name' : name, 'email': email, 'message': message, **request.data}
            serializer = ProductReviewsSerializer(data=data)

            if serializer.is_valid():
                serializer.save()  # Save the new ProductReview instance
                return Response({"success":True,"message":"Review Created Successfully"}, status=status.HTTP_201_CREATED)
            else:
                log_action("ERROR",f"Review creation failed: {serializer.errors}")
                return Response({"success":False,"message":"Review Couldn't Be Created, Try Again Later."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log the exception
            log_action("EXCEPTION","An error occurred during review creation.")
            # Optionally, you can also log the actual exception message
            # log_action("EXCEPTION",f"An error occurred during review creation: {e}")

            # Return a generic error response
            return Response({"success": False, "message": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, pk, *args, **kwargs):
        try:
            user = request.user
            # Check if the user is the owner of the review or if the user is staff
            review = ProductReviews.objects.get(id=pk)
            if user.is_staff:
                review.delete()  # Delete the review
                return Response({"success": True, "message": "Review Deleted Successfully"}, status=status.HTTP_204_NO_CONTENT)
            else:
                log_action("WARNING",f"Warning: A User tried to delete a review with no access!")
                return Response({"success": False, "message": "You are not authorized to delete this review."}, status=status.HTTP_403_FORBIDDEN)
        except ProductReviews.DoesNotExist:
            return Response({"success": False, "message": "Review not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_action("EXCEPTION",f"An error occurred during review deletion: {e}")
            # Return a generic error response
            return Response({"success": False, "message": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)