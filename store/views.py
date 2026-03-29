from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser , JSONParser
from rest_framework.permissions import AllowAny
from .models import Product, Category, Brand
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .serializers import ProductSerializer, CategorySerializer, BrandSerializer




@api_view(['GET'])
def category_list(request):
    categories = Category.objects.filter(parent__isnull=True)
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

def get_descendant_ids(category):
    ids = [category.id]
    for child in category.children.all():
        ids.extend(get_descendant_ids(child))
    return ids

@api_view(['GET'])
def products_by_category(request, slug):
    category = Category.objects.get(slug=slug)

    category_ids = get_descendant_ids(category)
    print("Category IDs fetched for slug:", slug, category_ids)

    products = Product.objects.filter(category_id__in=category_ids)

    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(http_method_names=["GET"])
@permission_classes([permissions.AllowAny])
def get_product(request,product_id):
    product = get_object_or_404(Product,pk=product_id)
    serializer = ProductSerializer(instance=product)
    response = {
        "message":"products",
        "data": serializer.data
    }

    return Response(data=response,status=status.HTTP_200_OK)
    


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def add_category(request):
    serializer = CategorySerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Category created successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def brand_list(request):
    brands = Brand.objects.all()
    serializer = BrandSerializer(brands, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)




@api_view(['GET'])
def product_list(request):
    queryset = Product.objects.all()

    category_slug = request.GET.get("category")
    search = request.GET.get("search")

    # Filter by category
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            return Response([])

        category_ids = get_descendant_ids(category)
        queryset = queryset.filter(category_id__in=category_ids)

    # 🔍 Filter by search
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    serializer = ProductSerializer(queryset, many=True)
    return Response(serializer.data)






@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@parser_classes([MultiPartParser, FormParser , JSONParser])
def add_product(request):
    serializer = ProductSerializer(
        data=request.data,
        context={"request": request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Product created successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def product_detail(request, slug):
    try:
        product = Product.objects.get(slug=slug, is_available=True)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ProductSerializer(
        product,
        context={"request": request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def add_brand(request):
    serializer = BrandSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Brand created successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    




