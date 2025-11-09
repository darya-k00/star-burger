import json
from django.http import JsonResponse
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Order, OrderItem, Restaurant

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
        if products_count == 0:
            errors.append('В базе данных нет продуктов для заказа')


        available_products = Product.objects.available().count()
        if available_products == 0:
            errors.append('Нет доступных продуктов для заказа')

        restaurants_count = Restaurant.objects.count()
        if restaurants_count == 0:
            errors.append('В базе данных нет ресторанов')

        restaurants_with_menu = Restaurant.objects.filter(menu_items__availability=True).distinct().count()
        if restaurants_with_menu == 0:
            errors.append('Нет ресторанов с доступным меню')

        if errors:
            return Response({
                'status': 'error',
                'message': 'Нельзя создать заказ',
                'errors': errors,
                'database_status': {
                    'total_products': products_count,
                    'available_products': available_products,
                    'total_restaurants': restaurants_count,
                    'restaurants_with_menu': restaurants_with_menu
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'ready',
            'message': 'Система готова к приему заказов',
            'database_status': {
                'total_products': products_count,
                'available_products': available_products,
                'total_restaurants': restaurants_count,
                'restaurants_with_menu': restaurants_with_menu
            },
            'required_fields': ['firstname', 'lastname', 'phonenumber', 'address', 'products'],
            'usage_example': {
                'method': 'POST',
                'url': '/api/order/',
                'body': {
                    'firstname': 'Иван',
                    'lastname': 'Петров',
                    'phonenumber': '+79161234567',
                    'address': 'ул. Ленина, 10',
                    'products': [{'product': 1, 'quantity': 2}]
                }
            }
        })

    elif request.method == 'POST':
        print("🟢 [API] Запрос регистрации заказа")
        print(f"🟢 Метод: {request.method}")
        print(f"🟢 Content-Type: {request.content_type}")

        try:
            if not request.data:
                print("Пустой запрос")
                return Response({
                    'status': 'error',
                    'message': 'Пустой запрос',
                    'errors': ['Тело запроса не может быть пустым'],
                    'debug': {'received_data': 'empty'}
                }, status=status.HTTP_400_BAD_REQUEST)

            data = request.data
            errors = []
            required_fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
            for field in required_fields:
                if field not in data:
                    error_msg = f'Обязательное поле "{field}" отсутствует'
                    errors.append(error_msg)
                    print(f" {error_msg}")

                elif not data[field]:
                    error_msg = f'Поле "{field}" не может быть пустым'
                    errors.append(error_msg)
                    print(f" {error_msg}")


            if 'firstname' in data and data['firstname']:
                firstname = data['firstname']
                if not isinstance(firstname, str) or len(firstname.strip()) < 2:
                    error_msg = 'Имя должно быть строкой минимум из 2 символов'
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
            if 'lastname' in data and data['lastname']:
                lastname = data['lastname']
                if not isinstance(lastname, str) or len(lastname.strip()) < 2:
                    error_msg = 'Фамилия должна быть строкой минимум из 2 символов'
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")

            if 'phonenumber' in data and data['phonenumber']:
                phonenumber = data['phonenumber']
                if not isinstance(phonenumber, str) or len(phonenumber.strip()) < 5:
                    error_msg = 'Номер телефона должен быть корректным'
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")

            if 'address' in data and data['address']:
                address = data['address']
                if not isinstance(address, str) or len(address.strip()) < 5:
                    error_msg = 'Адрес должен содержать минимум 5 символов'
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")

            if 'products' in data:
                products = data['products']
                if not isinstance(products, list):
                    error_msg = 'Поле "products" должно быть списком'
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
                elif not products:
                    error_msg = 'Список продуктов не может быть пустым'
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
                else:
                    print(f" Продукты: {products}")
                    for i, product_data in enumerate(products, 1):
                        product_errors = []

                        if not isinstance(product_data, dict):
                            error_msg = f'Продукт #{i}: должен быть объектом'
                            product_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                            continue

                        product_id = product_data.get('product')
                        quantity = product_data.get('quantity', 1)

                        print(f" Продукт #{i}: ID={product_id}, Количество={quantity}")

                        if product_id is None:
                            error_msg = f'Продукт #{i}: отсутствует ID продукта'
                            product_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                        elif not isinstance(product_id, int):
                            error_msg = f'Продукт #{i}: ID должен быть числом'
                            product_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                        elif product_id <= 0:
                            error_msg = f'Продукт #{i}: ID должен быть положительным числом'
                            product_errors.append(error_msg)
                            print(f"❌ {error_msg}")


                        if not isinstance(quantity, int):
                            error_msg = f'Продукт #{i}: количество должно быть числом'
                            product_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                        elif quantity < 1:
                            error_msg = f'Продукт #{i}: количество должно быть положительным'
                            product_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                        elif quantity > 100:
                            error_msg = f'Продукт #{i}: количество не может превышать 100'
                            product_errors.append(error_msg)
                            print(f"❌ {error_msg}")

                        if product_errors:
                            errors.extend(product_errors)


            if errors:
                print(f"❌ Найдены ошибки: {errors}")
                return Response({
                    'status': 'error',
                    'message': 'Невалидные данные заказа',
                    'errors': errors,
                    'received_data': data
                }, status=status.HTTP_400_BAD_REQUEST)


            print("НОВЫЙ ЗАКАЗ:")
            import json
            print(json.dumps(data, ensure_ascii=False, indent=2))

            order = Order.objects.create(
                firstname=data['firstname'].strip(),
                lastname=data['lastname'].strip(),
                phonenumber=data['phonenumber'].strip(),
                address=data['address'],.strip()
            )      

            missing_products = []
            valid_products = []

            for product_data in data['products']:
                product_id = product_data['product']
                quantity = product_data['quantity']

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
                        'quantity': quantity,
                        'price': str(product.price)
                    })
                    print(f"  Продукты:  {product.name}, Количество: {quantity}")
                except Product.DoesNotExist:
                    error_msg = f"Продукт с ID {product_id} не найден в базе данных"
                    missing_products.append({
                        'product_id': product_id,
                        'error': error_msg
                    })
                    print(f"  {error_msg}")
                except Exception as e:
                    error_msg = f"Ошибка  : {str(e)}"
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
                    'customer': {
                    'firstname': order.firstname,
                    'lastname': order.lastname,
                    'phonenumber': str(order.phonenumber),
                    'address': order.address
                    },
                    'added_products': valid_products,
                }

            if missing_products:
                    response_data['status'] = 'partial_success'
                    response_data['message'] = 'Заказ создан, но некоторые продукты отсутствуют'
                    response_data['missing_products'] = missing_products
                    return Response(response_data, status=status.HTTP_207_MULTI_STATUS)

            return Response(response_data)

        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return Response({
                'status': 'error',
                'message': 'Внутренняя ошибка сервера',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        return Response({
            'status': 'error',
            'message': 'Метод не разрешен',
            'errors': [f'Метод {request.method} не поддерживается']
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        