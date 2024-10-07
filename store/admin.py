from django.contrib import admin
from store.models import Product, Variation, ReviewRating, ProductGallery

import admin_thumbnails

@admin_thumbnails.thumbnail('image')
class ProductGalleryAdmin(admin.TabularInline):
    model = ProductGallery
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'price', 'stock', 'category', 'created_date', 'modified_date']
    prepopulated_fields = {'slug': ('product_name', )}
    inlines = [ProductGalleryAdmin]


class VariationAdmin(admin.ModelAdmin):
    list_display = ['product', 'variation_category', 'variation_value', 'is_active']
    list_editable = ['is_active']
    list_filter = ['product', 'variation_category', 'variation_value']


admin.site.register(Product, ProductAdmin)
admin.site.register(ProductGallery)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)