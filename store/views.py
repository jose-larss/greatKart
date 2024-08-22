from django.shortcuts import render, get_object_or_404
from store.models import Product
from category.models import Category


def product_detail(request, category_slug, product_slug):
    category = get_object_or_404(Category, slug = category_slug)
    single_product = get_object_or_404(Product, slug = product_slug, category = category)

    return render(request, "store/product-detail.html", {'single_product':single_product})


def store(request, category_slug = None):
    if category_slug != None:
        category = get_object_or_404(Category, slug = category_slug)
        products = Product.objects.filter(category = category, is_available = True)
    else:
        products = Product.objects.filter(is_available = True)

    return render(request, "store/store.html", {'products':products})
