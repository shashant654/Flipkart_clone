from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
User = get_user_model()  # This gets your CustomUser model
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login,logout 
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import random
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from datetime import datetime
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.core.mail import send_mail
from .forms import ContactForm
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import razorpay
from django.conf import settings




# def home(request):
#     products = Product.objects.all()[:8]
#     categories = Category.objects.all()  # If using a Category model
#     return render(request, 'home.html', {
#         'products': products,
#         'categories': categories
#     })


def home(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )[:8]
    else:
        products = Product.objects.all()[:8]
        
    categories = Category.objects.all()
    return render(request, 'home.html', {
        'products': products,
        'categories': categories,
        'search_query': query
    })



def register(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Basic validation
        if not first_name or not last_name or not email or not password:
            messages.error(request, 'All fields are required.')
            return redirect('/register/')

        # Email format validation
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email format.')
            return redirect('/register/')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return redirect('/register/')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('/register/')

        # Use email as username
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=email,
        )
        user.set_password(password)
        user.save()

        messages.success(request, 'Account created successfully.')
        return redirect('/login/')

    return render(request, 'register.html')

def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid email.')
            return redirect('/login/')

        user = authenticate(username=user.username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid password.')
            return render(request, 'login.html') 

    return render(request, 'login.html')  

#       ----------------------------------------- 
def logout_page(request):
      logout(request)
      return redirect('/login/')




@login_required
def my_profile(request):
    user = request.user
    addresses = Order.objects.filter(user=user).values('phone', 'address', 'city').distinct()

    return render(request, 'my_profile.html', {
        'user': user,
        # 'addresses': addresses
    })

    
@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.mobile_number = request.POST.get('mobile_number')
        user.alternate_number = request.POST.get('alternate_number')
        user.gender = request.POST.get('gender')
        user.dob = request.POST.get('dob')
        user.city = request.POST.get('city')
        user.state = request.POST.get('state')
        user.country = request.POST.get('country')
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('my_profile')

    return render(request, 'edit_profile.html', {
        'user': user,
        'GENDER_CHOICES': User.GENDER_CHOICES
    })




def about(request):
    return render(request, 'about.html')


def categories(request):
    categories = Category.objects.all()
    return render(request, 'categories.html', {'categories': categories})



# def category_products(request, category_id):
#     category = Category.objects.get(id=category_id)
#     products = category.products.all()
#     return render(request, 'category_products.html', {'category': category, 'products': products})


def category_products(request, category_id):
    category = Category.objects.get(id=category_id)
    query = request.GET.get('q')
    
    if query:
        products = category.products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    else:
        products = category.products.all()
        
    return render(request, 'category_products.html', {
        'category': category, 
        'products': products,
        'search_query': query
    })

from django.core.paginator import Paginator
from django.db.models import Q

def search_results(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    categories = Category.objects.none()
    
    if query:
        # Search products
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category').distinct()
        
        # Search categories
        categories = Category.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
        
        # Paginate products
        product_paginator = Paginator(products, 12)  # 12 products per page
        product_page_number = request.GET.get('product_page')
        product_page = product_paginator.get_page(product_page_number)
        
        # Paginate categories
        category_paginator = Paginator(categories, 6)  # 6 categories per page
        category_page_number = request.GET.get('category_page')
        category_page = category_paginator.get_page(category_page_number)
    else:
        product_page = None
        category_page = None
        
    return render(request, 'search_results.html', {
        'product_page': product_page,
        'category_page': category_page,
        'search_query': query,
        'has_results': (products.exists() or categories.exists())
    })

    
# def product_detail(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     return render(request, 'product_detail.html', {'product': product})

from django.shortcuts import get_object_or_404, render
from .models import Product

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Get related products (products from the same category, excluding current product)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(
        id=product.id
    )[:4]  # Limit to 4 related products
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)


# Wishlist Views
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if item already exists in wishlist
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f"{product.name} added to your wishlist!")
    else:
        messages.info(request, f"{product.name} is already in your wishlist!")
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    try:
        wishlist_item = Wishlist.objects.get(user=request.user, product=product)
        wishlist_item.delete()
        messages.success(request, f"{product.name} removed from your wishlist!")
    except Wishlist.DoesNotExist:
        messages.error(request, "This item is not in your wishlist.")
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

# Cart Views
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get or create cart for user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get or create cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 0}
    )
    
    if cart_item.quantity < product.quantity:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"{product.name} added to cart.")
    else:
        messages.error(request, f"Only {product.quantity} item(s) available in stock.")
    
    return redirect('cart')

@login_required
def update_cart(request, product_id, action):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(user=request.user)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        
        if action == 'increase':
            if cart_item.quantity < product.quantity:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"Added {product.name} to your cart.")
            else:
                messages.error(request, f"Only {product.quantity} item(s) available in stock.")
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                messages.success(request, f"Removed {product.name} from your cart.")
        
        return redirect('cart')
    
    except CartItem.DoesNotExist:
        messages.error(request, "This item is not in your cart.")
        return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(user=request.user)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f"Removed {product_name} from your cart.")
    except CartItem.DoesNotExist:
        messages.error(request, "This item is not in your cart.")
    
    return redirect('cart')

@login_required
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = []
    total_price = 0
    
    if cart:
        for item in cart.items.all():
            item_total = item.product.selling_price * item.quantity
            total_price += item_total
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'item_total': item_total
            })
    
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

# Checkout and Order Processing

@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            messages.info(request, "Your cart is empty.")
            return redirect('home')
        
        total_price = sum(item.product.selling_price * item.quantity for item in cart_items)

        # Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": int(total_price * 100),  # Amount in paise
            "currency": "INR",
            "payment_capture": "1"
        })

        context = {
            'cart_items': [{
                'product': item.product,
                'quantity': item.quantity,
                'item_total': item.product.selling_price * item.quantity
            } for item in cart_items],
            'total_price': total_price,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        }

        return render(request, 'checkout.html', context)

    except Cart.DoesNotExist:
        messages.info(request, "Your cart is empty.")
        return redirect('home')


def generate_tracking_number():
    trackno = 'Track_' + str(random.randint(1111111, 9999999))
    while Order.objects.filter(tracking_no=trackno).exists():
        trackno = 'Track_' + str(random.randint(1111111, 9999999))
    return trackno

def generate_order_id():
    order_id = 'Order_' + str(random.randint(1111111, 9999999))
    while Order.objects.filter(order_id=order_id).exists():
        order_id = 'Order_' + str(random.randint(1111111, 9999999))
    return order_id

def send_invoice_email(order, order_items):
    subject = f"Invoice for your Order {order.order_id}"
    recipient = [order.email]

    html_message = render_to_string("email/invoice_template.html", {
        'order': order,
        'order_items': order_items
    })

    email = EmailMessage(subject, html_message, to=recipient)
    email.content_subtype = 'html'
    email.send()

@login_required
@require_POST
def placeorder(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('checkout')

        # Fetch form data
        first_name = request.POST.get('fname', '').strip()
        last_name = request.POST.get('lname', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        payment_method = request.POST.get('payment', 'cod')
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')

        # Validate required fields
        if not all([first_name, last_name, email, phone, address, city]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('checkout')

        # Calculate total price
        total_price = sum(item.product.selling_price * item.quantity for item in cart_items)

        # Payment verification only for non-COD methods
        if payment_method != 'cod':
            if not razorpay_payment_id:
                messages.error(request, "Payment information missing for online payment.")
                return redirect('checkout')
                
            try:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                params = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                client.utility.verify_payment_signature(params)
                payment_status = 'Success'
            except razorpay.errors.SignatureVerificationError:
                messages.error(request, "Payment verification failed. Please try again.")
                return redirect('checkout')
            except Exception as e:
                messages.error(request, f"Payment processing error: {str(e)}")
                return redirect('checkout')
        else:
            payment_status = 'Pending'

        # Generate unique order and tracking IDs
        tracking_number = generate_tracking_number()
        order_id = generate_order_id()

        # Create the order
        order = Order.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            total_price=total_price,
            tracking_no=tracking_number,
            order_id=order_id,
            payment_method=payment_method,
            payment_id=razorpay_payment_id if payment_method != 'cod' else None,
            payment_status=payment_status,
            status='Pending'
        )

        # Create order items and reduce stock
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.selling_price
            )
            # Update product stock
            item.product.quantity -= item.quantity
            item.product.save()

        # Delete the cart after order is placed
        cart.delete()

        # Send invoice email
        send_invoice_email(order, OrderItem.objects.filter(order=order))

        messages.success(request, "Your order has been placed successfully!")
        return redirect('home', order_id=order.order_id)

    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('checkout')
    except Exception as e:
        messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('checkout')


# Order History Views
@login_required
def my_orders(request):
    order_list = Order.objects.filter(user=request.user).order_by('-created_at')

    # Get dates from query params
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Apply date filtering
    if from_date:
        order_list = order_list.filter(created_at__date__gte=parse_date(from_date))
    if to_date:
        order_list = order_list.filter(created_at__date__lte=parse_date(to_date))

    # Pagination
    paginator = Paginator(order_list, 5)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    context = {
        'orders': orders,
        'request': request
    }

    return render(request, 'my_orders.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items
    }
    
    return render(request, 'order_detail.html', context)


@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_cancel():
        messages.error(request, "This order cannot be cancelled.")
        return redirect('my_orders')
    
    # Update order status
    order.status = 'Cancelled'
    order.save()
    
    # Restore product quantities
    for item in order.orderitem_set.all():
        product = item.product
        product.quantity += item.quantity
        product.save()
    
    messages.success(request, "Your order has been cancelled successfully.")
    return redirect('my_orders')

@login_required
@require_POST
def cancel_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    if not order.can_cancel() or item.cancelled:
        messages.error(request, "This item cannot be cancelled.")
        return redirect('order_detail', order_id=order.id)
    
    # Mark item as cancelled
    item.cancelled = True
    item.cancelled_at = timezone.now()
    item.save()
    
    # Restore product quantity
    item.product.quantity += item.quantity
    item.product.save()
    
    # Update order total price
    order.total_price -= item.price * item.quantity
    order.save()
    
    # Check if all items are cancelled
    if not order.orderitem_set.filter(cancelled=False).exists():
        order.status = 'Cancelled'
        order.save()
    
    messages.success(request, f"{item.product.name} has been cancelled successfully.")
    return redirect('order_detail', order_id=order.id)



@login_required
def saved_address(request):
    user = request.user
    addresses = Order.objects.filter(user=user).values('first_name', 'last_name', 'email', 'phone', 'city', 'address').distinct()

    return render(request, 'saved_address.html', {
        'addresses': addresses
    })




def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()

            # Send email
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender = form.cleaned_data['email']
            name = form.cleaned_data['name']
            
            send_mail(
                subject=f"[Contact] {subject}",
                message=f"From: {name} <{sender}>\n\n{message}",
                from_email='your_email@example.com',  # Replace with your email
                recipient_list=['your_email@example.com'],  # Or site admin
                fail_silently=False,
            )

            messages.success(request, "Your message has been sent successfully.")
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})


from django.core.mail import send_mail

def send_test_email(request):
    subject = 'Test Email from Django'
    message = 'This is a test email sent from Gro Infotech Django app.'
    from_email = 'harmeet@groinfotech.com'
    recipient_list = ['shantidevi81992@gmail.com']

    try:
        send_mail(subject, message, from_email, recipient_list)
        return HttpResponse("✅ Test email sent successfully!")
    except Exception as e:
        return HttpResponse(f"❌ Failed to send email: {e}")


def faqs_view(request):
    return render(request, 'footer_files/faqs.html')

def shipping_policy_view(request):
    return render(request, 'footer_files/shipping_policy.html')

def return_policy_view(request):
    return render(request, 'footer_files/return_policy.html')

def privacy_policy_view(request):
    return render(request, 'footer_files/privacy_policy.html')