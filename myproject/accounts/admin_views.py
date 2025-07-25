from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator

from .models import Order, Product, Category


# Admin Dashboard View
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    user_count = User.objects.count()
    order_count = Order.objects.count()
    product_count = Product.objects.count()
    total_revenue = Order.objects.filter(status='Delivered').aggregate(
        total=Sum('total_price'))['total'] or 0

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    low_stock_products = Product.objects.filter(quantity__lt=10).order_by('quantity')[:5]

    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    daily_sales = Order.objects.filter(
        created_at__range=(start_date, end_date),
        status='Delivered'
    ).annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total_sales=Sum('total_price'),
        order_count=Count('id')
    ).order_by('day')

    top_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')[:5]

    recent_users = User.objects.order_by('-date_joined')[:5]

    # Get top selling categories
    top_categories = Category.objects.annotate(
        total_sold=Sum('products__orderitem__quantity')
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]  # Top 5 categories by items sold



    context = {
        'user_count': user_count,
        'order_count': order_count,
        'product_count': product_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'daily_sales': list(daily_sales),
        'top_products': top_products,
        'recent_users': recent_users,
        'sales_period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'top_categories': top_categories,
    }
    return render(request, 'admin/dashboard.html', context)


# Customer Management View
@user_passes_test(lambda u: u.is_superuser)
def customer_management(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')

    # Base queryset with annotation
    customers = User.objects.annotate(
        order_count=Count('order'),
        total_spent=Sum('order__total_price')
    ).order_by('-date_joined')

    if search_query:
        customers = customers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if status_filter == 'active':
        customers = customers.filter(is_active=True)
    elif status_filter == 'inactive':
        customers = customers.filter(is_active=False)

    # Count stats for the cards
    all_customers = User.objects.all()
    active_customers = all_customers.filter(is_active=True).count()
    from datetime import datetime
    now = datetime.now()
    new_this_month = all_customers.filter(date_joined__year=now.year, date_joined__month=now.month).count()

    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'active_customers': active_customers,
        'new_this_month': new_this_month,
    }

    return render(request, 'admin/customer_management.html', context)


# Inventory Management View
@user_passes_test(lambda u: u.is_superuser)
def inventory_management(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', 'all')
    stock_filter = request.GET.get('stock', 'all')

    products = Product.objects.select_related('category').annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('name')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_filter != 'all':
        products = products.filter(category_id=category_filter)

    if stock_filter == 'low':
        products = products.filter(quantity__lt=10)
    elif stock_filter == 'out':
        products = products.filter(quantity=0)

    # For stats cards
    all_products = Product.objects.all()
    low_stock_count = all_products.filter(quantity__lt=10).count()
    out_of_stock_count = all_products.filter(quantity=0).count()

    categories = Category.objects.all()

    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'stock_filter': stock_filter,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }

    return render(request, 'admin/inventory_management.html', context)

# Sales Analytics View
@user_passes_test(lambda u: u.is_superuser)
def sales_analytics(request):
    default_start = datetime.now() - timedelta(days=30)
    start_date = request.GET.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except (ValueError, TypeError):
        start_date = default_start
        end_date = datetime.now()

    daily_sales = Order.objects.filter(
        created_at__date__range=(start_date, end_date),
        status='Delivered'
    ).annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total_sales=Sum('total_price'),
        order_count=Count('id')
    ).order_by('day')

    monthly_sales = Order.objects.filter(
        created_at__date__range=(start_date, end_date),
        status='Delivered'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('total_price'),
        order_count=Count('id')
    ).order_by('month')

    top_products = Product.objects.filter(
        orderitem__order__created_at__date__range=(start_date, end_date),
        orderitem__order__status='Delivered'
    ).annotate(
        total_sold=Sum('orderitem__quantity'),
        revenue=Sum('orderitem__price')
    ).order_by('-total_sold')[:10]

    top_customers = User.objects.filter(
        order__created_at__date__range=(start_date, end_date),
        order__status='Delivered'
    ).annotate(
        total_spent=Sum('order__total_price'),
        order_count=Count('order')
    ).order_by('-total_spent')[:10]

    context = {
        'daily_sales': list(daily_sales),
        'monthly_sales': list(monthly_sales),
        'top_products': top_products,
        'top_customers': top_customers,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }

    return render(request, 'admin/sales_analytics.html', context)
