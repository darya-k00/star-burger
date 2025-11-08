import json
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import Product, Order, OrderItem

from phonenumber_field.phonenumber import to_python
from phonenumber_field.validators import validate_international_phonenumber
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view

@api_view(['GET'])
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

@csrf_exempt

def register_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)

    products = data.get('products')
    if not products:
        return JsonResponse({'error': 'Empty products'}, status=400)

    firstname = data.get('firstname', '').strip()
    lastname = data.get('lastname', '').strip()
    phonenumber = data.get('phonenumber', '').strip()
    address = data.get('address', '').strip()

    if not (firstname and phonenumber and address):
        return JsonResponse({'error': 'Не заполнены обязательные поля'}, status=400)

    # Валидация номера телефона
    try:
        phonenumber_obj = to_python(phonenumber)
        validate_international_phonenumber(phonenumber_obj)
    except ValidationError:
        return JsonResponse({'error': 'Номер телефона некорректный'}, status=400)

    with transaction.atomic():
        order = Order.objects.create(
            firstname=firstname,
            lastname=lastname,
            phonenumber=phonenumber,
            address=address
        )
        order_items = []
        for product_data in products:
            try:
                product = Product.objects.get(pk=product_data['product'])
            except Product.DoesNotExist:
                transaction.set_rollback(True)
                return JsonResponse({'error': f'Product not found: {product_data["product"]}'}, status=400)
            quantity = product_data.get('quantity', 1)
            item = OrderItem(
                order=order,
                product=product,
                quantity=quantity
            )
            order_items.append(item)
        OrderItem.objects.bulk_create(order_items)

    return JsonResponse({'status': 'ok', 'order_id': order.id})
