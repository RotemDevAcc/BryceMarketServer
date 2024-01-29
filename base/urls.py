from django.urls import path, include

from . import views
from .views import RegistrationView
from . import management
from .management import ProductsView, PManagemetView, UManagementView, CManagementView
from .recipemanager import RecommendRecipesAPIView
from .passwordreset import PasswordResetRequestView, PasswordResetConfirmView
from .contact import ContactCreateView
urlpatterns = [
    # path('', views.index),
    path('products/', ProductsView.as_view(), name='product-list'),
    path('productslist/',views.productlist),
    path('getcoupon/', views.getcoupon),

    #Management
    path('pmanagement/', PManagemetView.as_view(), name='product-manage'),
    path('pmanagement/<int:pk>/', PManagemetView.as_view(), name='product-managepk'),
    path('umanagement/', UManagementView.as_view(), name='user-manage'),
    path('umanagement/receipts/<int:pk>/',management.get_user_receipts, name='user-manage-receipts'),
    path('umanagement/set/', management.setstaff,name='set-staff'),
    path('umanagement/delete/<int:pk>/', management.deleteuser,name='delete-user'),
    path('cmanagement/', CManagementView.as_view(), name='user-manage'),
    path('getreceipts/', management.receipts),

    #Users
    path('login/', views.MyTokenObtainPairView.as_view()),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password_reset_confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('profile/',views.modprofile, name="profile-modify"),

    #AI
    path('api/recommend_recipes/', RecommendRecipesAPIView.as_view(), name='recommend_recipes_api'),


    #Contact
    path('contact/', ContactCreateView.as_view(), name='contact_form'),
    path('contact/<int:id>/', ContactCreateView.as_view(),name='delete_contact'),
]
