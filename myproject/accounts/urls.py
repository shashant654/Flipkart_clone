from django.urls import path

from .views import login_page,logout_page,register
from django.contrib.auth.models import User
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('login/',login_page,name="login_page"),
    path('logout/',logout_page,name='logout_page'),
    path('register/',register,name="register"),
    path('about/', about, name='about'),
    path('categories/', categories, name='categories'),	
    path('category/<int:category_id>/', category_products, name='category_products'),
    path('product/<int:pk>/details/', product_detail, name='product_detail'),

    path('cart/', cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/<str:action>/', update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout, name='checkout'),
    path('placeorder/', placeorder, name='placeorder'),
    path('my_profile/', my_profile, name='my_profile'),
    path('my_orders/', my_orders, name='my_orders'),
    path('order/<int:order_id>/',order_detail, name='order_detail'),
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('cancel-order-item/<int:order_id>/<int:item_id>/', cancel_order_item, name='cancel_order_item'),
    path('saved-address/', saved_address, name='saved_address'),
    path('contact/', contact, name='contact'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('send-test-email/', send_test_email, name='send_test_email'),
    path('faqs/', faqs_view, name='faqs'),
    path('shipping-policy/', shipping_policy_view, name='shipping_policy'),
    path('return-policy/', return_policy_view, name='return_policy'),
    path('privacy-policy/', privacy_policy_view, name='privacy_policy'),


    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', view_wishlist, name='view_wishlist'),
    path('search/', search_results, name='search_results'),
]



