from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializer import ContactSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAdminUser
from .models import Contact
from .logger import log_action

@permission_classes([IsAuthenticated])
class ContactCreateView(APIView):
    def get(self, request):
        try:
            user = request.user

            if(user and not user.is_staff):
                return Response({"success":False,"messsage":"Internal Server Error"}, status=status.HTTP_403_FORBIDDEN)
            # Fetch all contacts from the database
            contacts = Contact.objects.all()
            
            # Serialize the contacts using your ContactSerializer
            serializer = ContactSerializer(contacts, many=True)
            
            # Return the serialized contacts as a JSON response
            return Response({"success":True , 'message': "Messages Delivered Successfully", "data": serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            log_action("ERROR",f"An exception occurred while fetching the contacts: {str(e)}")
            return Response({"success": False,'message': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, format=None):
        try:
            # Access the authenticated user and their email address
            user = request.user
            email = user.email
            name = f"{user.firstname} {user.lastname}"

            # Create a new dictionary with the user's email, message, and other data
            data = {'name' : name, 'email': email, 'message': request.data.get('message', ''), **request.data}
            # Pass the updated data to the serializer
            serializer = ContactSerializer(data=data)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                errors = serializer.errors
                log_action("ERROR",f"Failed to create a new contact: {errors}")
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_action("ERROR",f"An exception occurred while creating a new contact: {str(e)}")
            return Response({'detail': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, id=None):
        try:
            user = request.user
            if(user and not user.is_staff):
                return Response({"success":False,"messsage":"Internal Server Error"}, status=status.HTTP_403_FORBIDDEN)
            # Check if the contact exists
            try:
                contact = Contact.objects.get(id=id)
            except Contact.DoesNotExist:
                return Response({"success":False,'message': 'Contact not found'}, status=status.HTTP_404_NOT_FOUND)

            # Perform the delete operation
            contact.delete()

            # Return a success response
            return Response({"success":True,'message': 'Contact deleted successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            log_action("ERROR",f"An exception occurred while deleting the contact: {str(e)}")
            return Response({"success":False,'message': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)