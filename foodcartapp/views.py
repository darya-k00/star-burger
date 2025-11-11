import json
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Product, Order, OrderItem, Restaurant
from .serializers import OrderSerializer

from rest_framework.decorators import api_view


def banners_list_api(request):
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


@csrf_exempt
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
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            print(f" Заказ #{order.id} создан")

            order_items = order.items.all()
            products_info = []
            for item in order_items:
                products_info.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': str(item.price)
                })


            return Response({
                    'order_id': order.id,
                    'status': 'success',
                    'message': 'Заказ успешно создан',
                    'customer': {
                    'firstname': order.firstname,
                    'lastname': order.lastname,
                    'phonenumber': str(order.phonenumber),
                    'address': order.address
                },
                'products': products_info,
                'order_total': str(sum(item.price * item.quantity for item in order_items))
            })


            print(f"❌ Ошибки валидации: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Невалидные данные заказа',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)