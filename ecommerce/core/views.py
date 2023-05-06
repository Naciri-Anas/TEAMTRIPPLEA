from django.shortcuts import render, redirect
from core.forms import *
from django.contrib import messages
from core.models import *
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .forms import CheckoutForm
from .models import CheckoutAddress
from django.conf import settings
from django.http import HttpResponse
from .models import Order
from django.views.decorators.csrf import csrf_exempt
import paypalrestsdk


# paypal_client =paypalrestsdk.configure.Config(
# auth=(settings.PAYPAL_ID, settings.PAYPAL_SECRET))

#paypal_client = paypalrestsdk.configure({
    #"mode": "sandbox",  # Set to 'live' for production
    #"client_id": settings.PAYPAL_ID,
    #"client_secret": settings.PAYPAL_SECRET
#})



# Create your views here.
def index(request):
    products = Product.objects.all()
    return render(request, 'core/index.html', {'products': products})


def orderlist(request):
    if Order.objects.filter(user=request.user, ordered=False).exists():
        order = Order.objects.get(user=request.user, ordered=False)
        return render(request, "core/orderlist.html", {"order": order})
    return render(request, "core/orderlist.html", {"message": "Your Cart is Empty"})


def add_product(request):

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            print('True')
            form.save()
            print("Data Saved Succcessfully")
            messages.success(request, "Product Added successfully")
            return redirect('/')
        else:
            print("Not Working")
            messages.info("Product is not Added,Try Again")
    else:

        form = ProductForm()
    return render(request, 'core/add_product.html', {'form': form})


def product_desc(request, pk):
    product = Product.objects.get(pk=pk)
    return render(request, 'core/product_desc.html', {'product': product})


def add_to_cart(request, pk):
    product = Product.objects.get(pk=pk)
    order_item, created = OrderItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False,

    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Added Quantity Item")
            return redirect("product_desc", pk=pk)
        else:
            order.items.add(order_item)
            messages.info(request, "Item added to cart")
            return redirect("product_desc", pk=pk)

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item added to cart")
        return redirect("product_desc", pk=pk)


def add_item(request, pk):
    product = Product.objects.get(pk=pk)
    order_item, created = OrderItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False,

    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            if order_item.quantity < product.product_available_count:
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "added Quantity Item")
                return redirect("orderlist")
            else:

                messages.info(request, "Item added to cart")
                return redirect("orderlist")

        else:
            order.items.add(order_item)
            messages.info(request, "Item added to cart")
            return redirect("product_desc", pk=pk)

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item added to cart")
        return redirect("product_desc", pk=pk)


def remove_item(request, pk):
    item = get_object_or_404(Product, pk=pk)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk=pk).exists():
            order_item = OrderItem.objects.filter(
                product=item,
                user=request.user,
                ordered=False,

            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
                messages.info(request, "Item quantity was updated")
                return redirect("orderlist")
        else:
            messages.info(request, "this item is not in your cart")
            return redirect("orderlist")
    else:
        messages.info(request, "you don't have any order")
        return redirect("orderlist")


def payment(request):
   return render(request,"core/paymentsummarypaypal.html")

def checkout_page(request):
    if CheckoutAddress.objects.filter(user=request.user).exists():
        return render(request, "core/checkout_address.html", {"payment_allow": "allow"})

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            street_address = form.cleaned_data.get("street_address")
            apartment_address = form.cleaned_data.get("apartment_address")
            country = form.cleaned_data.get("country")
            zip_code = form.cleaned_data.get("zip")

            checkout_address = CheckoutAddress(
                user=request.user,
                street_address=street_address,
                apartment_address=apartment_address,
                country=country,
                zip_code=zip_code
            )
            checkout_address.save()
            print("It should render the summary page")
            return render(request, "core/checkout_address.html", {"payment_allow": "allow"})
        else:
            messages.warning(request, "Failed checkout")
            form = CheckoutForm()

    else:
        form = CheckoutForm()

    return render(request, "core/checkout_address.html", {"form": form})

