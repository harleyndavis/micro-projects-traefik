from django.conf import settings


def assets_url(request):
    return {'ASSETS_URL': settings.ASSETS_URL}
