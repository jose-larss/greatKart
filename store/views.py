from django.shortcuts import render, get_object_or_404, HttpResponse
from store.models import Product
from category.models import Category
from cart.models import CartItem

from cart.views import _cart_id

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q


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

    return render(request, "store/product-detail.html", {'single_product':single_product, 
                                                         'in_cart':in_cart})


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
