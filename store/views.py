from django.db.models import Q
from django.contrib import messages

from django.shortcuts import render, get_object_or_404, HttpResponse, redirect
from store.models import Product, ReviewRating, ProductGallery
from category.models import Category
from cart.models import CartItem
from orders.models import Order, OrderProduct

from store.forms import ReviewForm

from cart.views import _cart_id

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')

    if request.method == "POST":
        product = Product.objects.get(id=product_id)

        try:
            review = ReviewRating.objects.get(user=request.user, product=product)
            form = ReviewForm(request.POST, instance=review) # Updated the review
            form.save()
            messages.success(request, "Thank you! Your review has been Updated.")

            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)

            if form.is_valid():
                data = form.save(commit=False)
                data.ip = request.META.get('REMOTE_ADDR')
                data.product = product
                data.user = request.user
                data.save()
                messages.success(request, "Thank you! Your review has been Submitted.")

                return redirect(url)            


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword)).order_by('-created_date')
    
    return render(request, 'store/store.html', {'products':products})


def product_detail(request, category_slug, product_slug):
    category = get_object_or_404(Category, slug = category_slug)
    single_product = get_object_or_404(Product, slug = product_slug, category = category)
    in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product)

    # Aqui hay que controlar si el usuario esta logado
    if request.user.is_authenticated:
        try:
            order_product = OrderProduct.objects.filter(user=request.user, product=single_product).exists()
        except OrderProduct.DoesNotExist:
            order_product = False
    else:
        order_product = False

    # Set the reviews
    reviews = ReviewRating.objects.filter(product = single_product, status=True)

    # Get the product Gallery
    product_gallery = ProductGallery.objects.filter(product=single_product)

    return render(request, "store/product-detail.html", {'single_product':single_product, 
                                                         'in_cart':in_cart,
                                                         'order_product':order_product,
                                                         'reviews':reviews,
                                                         'product_gallery':product_gallery})


def store(request, category_slug = None):
    if category_slug != None:
        category = get_object_or_404(Category, slug = category_slug)
        products = Product.objects.filter(category = category, is_available = True)
    else:
        products = Product.objects.filter(is_available = True)

    # Se implementa la paginación
    paginator = Paginator(products, 1) # 6 productos por pagina
    page_number = request.GET.get('page') 
    page_products = paginator.get_page(page_number)

    return render(request, "store/store.html", {'products':page_products})
