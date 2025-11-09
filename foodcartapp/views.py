import json
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Order, OrderItem, Restaurant
from .serializers import OrderSerializer

from rest_framework.decorators import api_view


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['GET', 'POST'])
def register_order(request):
    if request.method == 'GET':
        errors = []

        products_count = Product.objects.count()
        
        restaurants_count = Restaurant.objects.count()
        
        if errors:
            return Response({'status': 'ready'})

    elif request.method == 'POST':
        print(" [API] Запрос регистрации заказа")

    import json
        print("📦 ЗАКАЗ (JSON):")
        print(json.dumps(request.data, ensure_ascii=False, indent=2))
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            print(f" Заказ #{order.id} создан")

  

            return Response({
                    'order_id': order.id,
                    'status': 'success',
                    'message': 'Заказ успешно создан'
            })
            print(f"❌ Ошибки валидации: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Невалидные данные заказа',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)