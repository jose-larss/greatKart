from django.shortcuts import render
from store.models import Product, ReviewRating

def home(request):
    products = Product.objects.filter(is_available=True).order_by('-created_date')

    # Set the reviews
    for product in products:
        reviews = ReviewRating.objects.filter(product = product, status=True)

    return render(request, "home.html", {'products':products, 
                                         'reviews':reviews})