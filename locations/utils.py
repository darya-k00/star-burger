from .models import Location
from .geocoder import fetch_coordinates
from django.conf import settings
from django.utils import timezone


def get_or_create_location(address):
    if not address:
        return None

    normalized_address = address.strip()

    location, created = Location.objects.get_or_create(
        address=normalized_address,
        defaults={}
    )

    if created:
        try:
            coords = fetch_coordinates(settings.YANDEX_GEOCODER_APIKEY, normalized_address)
            if coords:
                location.longitude, location.latitude = coords
            location.last_geocode_attempt = timezone.now()
            location.save()
        except Exception as e:
            print(f"Ошибка геокодирования для адреса {normalized_address}: {e}")

    return location


def batch_update_locations(addresses):
    locations = []
    for address in addresses:
        if address:
            location = get_or_create_location(address)
            if location:
                locations.append(location)
    return locations