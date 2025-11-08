import json
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import Product, Order, OrderItem

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


@api_view(['POST'])
def register_order(request):
    if request.method != 'POST':

        try:
            data = request.data
            print("НОВЫЙ ЗАКАЗ:")
            import json
            print(json.dumps(data, ensure_ascii=False, indent=2))

            order = Order.objects.create(
                firstname=data['firstname'],
                lastname=data['lastname'],
                phonenumber=data['phonenumber'],
                address=data['address'],
            )      

            missing_products = []
            valid_products = []

            for product_data in data.get('products', []):
                if isinstance(product_data, dict):
                    product_id = product_data.get('product')
                    quantity = product_data.get('quantity', 1)
                elif isinstance(product_data, str):
                    try:
                        if ':' in product_data:
                            product_id, quantity = product_data.split(':', 1)
                        else:
                            product_id = product_data
                            quantity = 1
                        product_id = int(product_id.strip())
                        quantity = int(quantity.strip()) if quantity else 1
                    except (ValueError, AttributeError):
                        print(f"  ❌ Ошибка парсинга строки: {product_data}")
                        continue
                else:
                    continue
                if not product_id:
                    continue
                try:
                    product = Product.objects.get(id=product_id)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price
                    )
                    valid_products.append({
                        'id': product_id,
                        'name': product.name,
                        'quantity': quantity
                    })
                    print(f"  Продукт ID: {product_id}, Количество: {quantity}")
                except Product.DoesNotExist:
                    error_msg = f"Продукт с ID {product_id} не найден в базе данных"
                    missing_products.append({
                        'product_id': product_id,
                        'error': error_msg
                    })
                    print(f"  {error_msg}")
                except Exception as e:
                    error_msg = f"Ошибка обработки продукта {product_id}: {str(e)}"
                    missing_products.append({
                        'product_id': product_id,
                        'error': error_msg
                    })
                    print(f"  {error_msg}")

            print(f" Заказ #{order.id} сохранен в БД")

            response_data = {
                    'order_id': order.id,
                    'status': 'success',
                    'message': 'Заказ создан',
                    'added_products': valid_products,
                }
            if missing_products:
                    response_data['status'] = 'partial_success'
                    response_data['message'] = 'Заказ создан, но некоторые продукты отсутствуют'
                    response_data['missing_products'] = missing_products
                    return JsonResponse(response_data, status=207)  # Multi-Status

            return JsonResponse(response_data)

        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Внутренняя ошибка сервера',
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Use POST method'}, status=400)
            
        