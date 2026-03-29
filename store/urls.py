from django.urls import path
from .views import (
    category_list,
    brand_list,
    product_list,
    product_detail,
    add_category,
    add_product,
    add_brand,
    products_by_category,
    get_product,
)

urlpatterns = [
    # 📂 Categories
    path("categories/", category_list, name="category-list"),
    path("categories/add/", add_category, name="category-add"),
    path("products/category/<slug:slug>/", products_by_category),

    # 🏷 Brands
    path("brands/", brand_list, name="brand-list"),
    path("brands/add/", add_brand, name="brand-add"),

    # 📦 Products
    path("products/", product_list, name="product-list"),
    path("products/add/", add_product, name="product-add"),

    # ⚠️ Order matters
    path("products/<int:product_id>/", get_product, name="get-product"),
    path("products/<slug:slug>/", product_detail, name="product-detail"),
]