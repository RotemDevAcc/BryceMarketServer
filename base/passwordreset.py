from .models import MarketUser
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import os
from django.contrib.auth.models import update_last_login
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.exceptions import ValidationError

class PasswordResetRequestView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        try:
            user = MarketUser.objects.get(email=email)
            token = default_token_generator.make_token(user)
            reset_link = f"http://localhost:3000/reset-password/{user.pk}/{token}"

            send_mail(
                'Password Reset Request',
                f'Please go to the following link to reset your password: {reset_link}',
                os.environ.get("EMAIL_HOST_USER"),  # Sender's email from environment variable
                [email],
                fail_silently=False,
            )
            return Response({"message": "If an account with that email exists, a password reset link has been sent."}, status=status.HTTP_200_OK)
        except MarketUser.DoesNotExist:
            # Mimicking the behavior of your old function
            return Response({'message': f'Password Recovery Sent To {email}'})
        except Exception as e:
            # Catching any other errors
            return Response({'message': "Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)
        

class PasswordResetConfirmView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            print("Received request data:", request.data)

            # Directly use the user ID from the request
            user_id = request.data.get("userId")
            print("User ID:", user_id)

            token = request.data.get("token")
            new_password = request.data.get("newPassword")

            user = MarketUser.objects.get(pk=user_id)
            print("User retrieved:", user)

            if not default_token_generator.check_token(user, token):
                print("Token check failed")
                return Response({"error": "Invalid or expired password reset token."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            
            # Optionally, update the last login time for the user
            update_last_login(None, user)

            print("Password reset successful")
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        except (TypeError, ValueError, OverflowError, MarketUser.DoesNotExist, ValidationError) as e:
            print("An error occurred:", str(e))
            return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)
