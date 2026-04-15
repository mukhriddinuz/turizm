from django.conf import settings
from django.utils import translation


class AdminUzbekLocaleMiddleware:
    """
    Force Uzbek locale inside the admin panel.

    LocaleMiddleware normally prioritizes the browser's Accept-Language header,
    which makes the admin appear in Russian for RU-configured browsers. For the
    admin UI we always prefer Uzbek so the panel stays consistent.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = f"/{str(settings.ADMIN_URL).lstrip('/')}"

        if request.path.startswith(admin_path):
            with translation.override('uz'):
                request.LANGUAGE_CODE = 'uz'
                return self.get_response(request)

        return self.get_response(request)
