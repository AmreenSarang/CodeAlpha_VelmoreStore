from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Product, Order, OrderItem
from .forms import RegisterForm, CheckoutForm
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.db.models import Sum
# -------------------------
# CART HELPERS
# -------------------------

def get_cart_items(request):
    """Return valid cart items and a total calculated from database prices."""
    session_cart = request.session.get('cart', {})
    cart_items = []
    cleaned_cart = {}
    total = Decimal('0.00')

    if not isinstance(session_cart, dict):
        request.session['cart'] = {}
        request.session.modified = True
        return cart_items, total

    for product_id, quantity in session_cart.items():
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if product_id <= 0 or quantity <= 0:
            continue

        product = Product.objects.filter(id=product_id).first()

        if product is None or product.stock <= 0:
            continue

        quantity = min(quantity, product.stock)
        cleaned_cart[str(product.id)] = quantity

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    if cleaned_cart != session_cart:
        request.session['cart'] = cleaned_cart
        request.session.modified = True

    return cart_items, total


# -------------------------
# HOME PAGE
# -------------------------

def home(request):
    products = Product.objects.all().order_by('-created_at')

    return render(
        request,
        'home.html',
        {'products': products}
    )


# -------------------------
# PRODUCT DETAILS
# -------------------------

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    return render(
        request,
        'product_detail.html',
        {'product': product}
    )


# -------------------------
# ADD TO CART
# -------------------------

@require_POST
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    if product.stock <= 0:
        messages.error(request, 'Sorry, this product is out of stock.')
        return redirect('product_detail', id=id)

    cart = request.session.get('cart', {})

    if not isinstance(cart, dict):
        cart = {}

    try:
        current_quantity = int(cart.get(str(product.id), 0))
    except (TypeError, ValueError):
        current_quantity = 0

    current_quantity = max(current_quantity, 0)

    if current_quantity >= product.stock:
        messages.warning(
            request,
            'You cannot add more than the available stock.'
        )
        return redirect('cart')

    cart[str(product.id)] = current_quantity + 1
    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, 'Product added to your cart.')
    return redirect('cart')


# -------------------------
# VIEW CART
# -------------------------

def cart(request):
    cart_items, total = get_cart_items(request)

    return render(
        request,
        'cart.html',
        {
            'cart_items': cart_items,
            'total': total,
        }
    )


# -------------------------
# REMOVE FROM CART
# -------------------------

@require_POST
def remove_from_cart(request, id):
    cart = request.session.get('cart', {})

    if not isinstance(cart, dict):
        cart = {}

    cart.pop(str(id), None)

    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, 'Product removed from your cart.')
    return redirect('cart')


# -------------------------
# INCREASE QUANTITY
# -------------------------

@require_POST
def increase_quantity(request, id):
    product = get_object_or_404(Product, id=id)

    cart = request.session.get('cart', {})

    if not isinstance(cart, dict):
        cart = {}

    product_id = str(product.id)

    try:
        quantity = int(cart.get(product_id, 0))
    except (TypeError, ValueError):
        quantity = 0

    if quantity < 0:
        quantity = 0

    if product.stock <= 0:
        cart.pop(product_id, None)
        messages.warning(request, 'This product is out of stock.')

    elif quantity < product.stock:
        cart[product_id] = quantity + 1
        messages.success(request, 'Cart quantity updated.')

    else:
        cart[product_id] = min(quantity, product.stock)
        messages.warning(request, 'No more stock is available.')

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


# -------------------------
# DECREASE QUANTITY
# -------------------------

@require_POST
def decrease_quantity(request, id):
    cart = request.session.get('cart', {})

    if not isinstance(cart, dict):
        cart = {}

    product_id = str(id)

    try:
        quantity = int(cart.get(product_id, 0))
    except (TypeError, ValueError):
        quantity = 0

    if quantity > 1:
        cart[product_id] = quantity - 1
    else:
        cart.pop(product_id, None)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


# -------------------------
# REGISTER
# -------------------------

def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                'Your account has been created successfully.'
            )
            return redirect('home')
    else:
        form = RegisterForm()

    return render(
        request,
        'register.html',
        {'form': form}
    )


# -------------------------
# LOGIN
# -------------------------


def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account is inactive.')
                return render(request, 'login.html')

            login(request, user)

            if user.is_staff:
                return redirect('admin_dashboard')

            return redirect('home')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')



# -------------------------
# LOGOUT
# -------------------------

@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')

    return redirect('home')


# -------------------------
# CHECKOUT
# -------------------------

@login_required
def checkout(request):
    cart_items, total = get_cart_items(request)

    if not cart_items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    locked_products = {}
                    validated_items = []
                    final_total = Decimal('0.00')

                    # Recheck stock using current database values.
                    for item in cart_items:
                        product_id = item['product'].id

                        product = Product.objects.select_for_update().get(
                            id=product_id
                        )

                        quantity = item['quantity']

                        if product.stock < quantity:
                            raise ValueError(
                                f'Not enough stock for {product.name}. '
                                'Please update your cart.'
                            )

                        locked_products[product.id] = product

                        subtotal = product.price * quantity
                        final_total += subtotal

                        validated_items.append({
                            'product': product,
                            'quantity': quantity,
                            'price': product.price,
                        })

                    # Create the order using server-calculated total.
                    order = Order.objects.create(
                        user=request.user,
                        full_name=form.cleaned_data['full_name'],
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data['phone'],
                        address=form.cleaned_data['address'],
                        city=form.cleaned_data['city'],
                        pincode=form.cleaned_data['pincode'],
                        total_amount=final_total,
                        status='Pending',
                    )

                    for item in validated_items:
                        product = locked_products[item['product'].id]
                        quantity = item['quantity']

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=item['price'],
                        )

                        product.stock -= quantity
                        product.save(update_fields=['stock'])

                # Clear the cart only after the transaction succeeds.
                request.session['cart'] = {}
                request.session.modified = True

                return redirect(
                    'order_success',
                    order_id=order.id
                )

            except Product.DoesNotExist:
                messages.error(
                    request,
                    'A product is no longer available. Please review your cart.'
                )
                return redirect('cart')

            except ValueError as error:
                messages.error(request, str(error))
                return redirect('cart')

    else:
        initial_data = {
            'email': request.user.email,
            'full_name': request.user.get_full_name(),
        }

        form = CheckoutForm(initial=initial_data)

    return render(
        request,
        'checkout.html',
        {
            'form': form,
            'cart_items': cart_items,
            'total': total,
        }
    )


# -------------------------
# ORDER SUCCESS
# -------------------------

@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        'order_success.html',
        {'order': order}
    )


# -------------------------
# MY ORDERS
# -------------------------

@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'orders.html',
        {'orders': orders}
    )
@staff_member_required(login_url='/admin/login/')
def admin_dashboard(request):
    today = timezone.localdate()

    # Main statistics
    product_count = Product.objects.count()
    customer_count = User.objects.filter(is_staff=False).count()
    order_count = Order.objects.count()

    total_revenue = (
        Order.objects.exclude(status='Cancelled')
        .aggregate(total=Sum('total_amount'))['total'] or 0
    )

    today_orders = Order.objects.filter(
        created_at__date=today
    ).count()

    today_revenue = (
        Order.objects.filter(created_at__date=today)
        .exclude(status='Cancelled')
        .aggregate(total=Sum('total_amount'))['total'] or 0
    )

    # Order status counts
    pending_orders = Order.objects.filter(status='Pending').count()
    confirmed_orders = Order.objects.filter(status='Confirmed').count()
    shipped_orders = Order.objects.filter(status='Shipped').count()
    delivered_orders = Order.objects.filter(status='Delivered').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()

    # Inventory alerts
    low_stock_products = Product.objects.filter(
        stock__gt=0,
        stock__lte=5
    ).order_by('stock', 'name')

    out_of_stock_count = Product.objects.filter(stock__lte=0).count()

    # Recent orders
    recent_orders = (
        Order.objects.select_related('user')
        .prefetch_related('items__product')
        .order_by('-created_at')[:8]
    )

    # Sales for the last seven calendar days
    daily_sales = []

    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)

        total = (
            Order.objects.filter(created_at__date=day)
            .exclude(status='Cancelled')
            .aggregate(total=Sum('total_amount'))['total'] or 0
        )

        daily_sales.append({
            'label': day.strftime('%a'),
            'date': day,
            'total': total,
        })

    highest_sales = max(
        (float(day['total']) for day in daily_sales),
        default=0
    )

    for day in daily_sales:
        if highest_sales > 0 and day['total'] > 0:
            day['bar_height'] = max(
                6,
                int(float(day['total']) / highest_sales * 100)
            )
        else:
            day['bar_height'] = 0

    context = {
        'product_count': product_count,
        'customer_count': customer_count,
        'order_count': order_count,
        'total_revenue': total_revenue,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock_count,
        'recent_orders': recent_orders,
        'daily_sales': daily_sales,
    }

    return render(request, 'admin_dashboard.html', context)