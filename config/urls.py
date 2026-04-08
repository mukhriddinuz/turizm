from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from django.views.static import serve
from django.http import HttpResponse, JsonResponse
from xml.sax.saxutils import escape

import platform
import django
from django.http import JsonResponse
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.utils import timezone

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency fallback
    psutil = None

from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView
)

# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi


def health_check(request):
    """Server va tizim ishlash holatini tekshirish uchun"""
    
    # Database status
    db_status = {}
    for alias in connections:
        try:
            connections[alias].cursor()
            db_status[alias] = "ok"
        except OperationalError:
            db_status[alias] = "failed"

    # Server va tizim info
    system_info = {
        'os': platform.system(),
        'os_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_cores': psutil.cpu_count(logical=True) if psutil else None,
        'memory_total_mb': round(psutil.virtual_memory().total / (1024 * 1024), 2) if psutil else None,
        'python_version': platform.python_version(),
        'django_version': django.get_version(),
    }

    return JsonResponse({
        'status': 'ok',
        'message': 'Server is running',
        'database': db_status,
        'system_info': system_info
    })


# API root view
def api_root(request):
    """API asosiy sahifasi - barcha endpointlar ro'yxati"""
    return JsonResponse({
        'message': 'Django REST API - v1.0',
        'endpoints': {
            'admin': f'/{settings.ADMIN_URL}',
            'api_documentation': '/api/docs/',
            'redoc': '/api/redoc/',
            'health_check': '/health/',
            'authentication': {
                'token_obtain': '/api/auth/token/',
                'token_refresh': '/api/auth/token/refresh/',
                'token_verify': '/api/auth/token/verify/',
                'token_blacklist': '/api/auth/token/blacklist/',
            },
            'api_v1': {
                'accounts': '/api/v1/accounts/',
                'main': '/api/v1/',
                'about': '/api/v1/about/',
                'culture': '/api/v1/culture/',
                'search_global': '/api/v1/search/global/',
                'seo_meta': '/api/v1/seo/meta/',
            }
        },
        'seo_files': {
            'robots': '/robots.txt',
            'sitemap': '/sitemap.xml',
        },
    })


def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /api/docs/login/",
            "Disallow: /api/docs/logout/",
            f"Sitemap: {sitemap_url}",
        ]
    )
    return HttpResponse(content, content_type='text/plain; charset=utf-8')


def _get_sitemap_base_url(request):
    frontend_base_url = str(getattr(settings, 'FRONTEND_BASE_URL', '')).strip().rstrip('/')
    if frontend_base_url:
        return frontend_base_url
    return request.build_absolute_uri('/').rstrip('/')


def sitemap_xml(request):
    base_url = _get_sitemap_base_url(request)
    today = timezone.now().date().isoformat()
    urls = [
        (f'{base_url}/', today, 'daily', '1.0'),
        (f'{base_url}/about/', today, 'weekly', '0.9'),
        (f'{base_url}/search/', today, 'daily', '0.7'),
    ]

    try:
        from apps.main.models import Destination, Region, RouteGuide

        for slug in Destination.objects.filter(is_active=True, region__is_active=True).values_list('slug', flat=True):
            urls.append((f'{base_url}/places/{slug}/', today, 'weekly', '0.8'))

        for slug in Region.objects.filter(is_active=True).values_list('slug', flat=True):
            urls.append((f'{base_url}/regions/{slug}/', today, 'weekly', '0.7'))

        for route_id in RouteGuide.objects.filter(is_active=True, destination__is_active=True).values_list('id', flat=True):
            urls.append((f'{base_url}/routes/{route_id}/', today, 'weekly', '0.7'))
    except Exception:
        # DB tayyor bo'lmagan muhitlarda ham sitemap endpoint ishlashi uchun.
        pass

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, changefreq, priority in urls:
        xml_parts.extend(
            [
                "<url>",
                f"<loc>{escape(loc)}</loc>",
                f"<lastmod>{lastmod}</lastmod>",
                f"<changefreq>{changefreq}</changefreq>",
                f"<priority>{priority}</priority>",
                "</url>",
            ]
        )
    xml_parts.append("</urlset>")
    return HttpResponse("".join(xml_parts), content_type='application/xml; charset=utf-8')


# Swagger/OpenAPI Schema (drf-yasg)
# schema_view = get_schema_view(
#     openapi.Info(
#         title="Django REST API",
#         default_version='v1',
#         description="""
#         # Django REST API Documentation
#         
#         Django 6.0 asosida qurilgan to'liq funksional REST API.
#         
#         ## Imkoniyatlar
#         - 🔐 JWT Authentication (Access & Refresh tokens)
#         - 👤 Foydalanuvchi boshqaruvi
#         - 📝 CRUD operatsiyalar
#         - 📤 Fayl yuklash
#         - 🔍 Qidiruv va filterlash
#         - 📄 Pagination
#         - 🌍 Ko'p tillilik (O'zbek, Rus, Ingliz)
#         - ⚡ Background tasks
#         
#         ## Autentifikatsiya
#         Token olish uchun `/api/auth/token/` endpointiga so'rov jo'nating va keyin har bir so'rovda Authorization headerda foydalaning:
#         ```
#         Authorization: Bearer <sizning_tokeningiz>
#         ```
#         
#         ## Rate Limiting
#         - Anonim foydalanuvchilar: 100 so'rov/soat
#         - Autentifikatsiya qilingan: 1000 so'rov/soat
#         
#         ## Xatoliklar
#         Barcha xatoliklar quyidagi formatda qaytariladi:
#         ```json
#         {
#             "success": false,
#             "error": {
#                 "code": "not_found",
#                 "message": "Resurs topilmadi",
#                 "details": {...}
#             },
#             "data": null
#         }
#         ```
#         
#         ## Versiyalash
#         API versiyasi URL da ko'rsatilgan: `/api/v1/`
#         
#         ---
#         **Muallif:** Your Name  
#         **Email:** contact@example.com  
#         **Sana:** 2024
#         """,
#         terms_of_service="https://www.example.com/terms/",
#         contact=openapi.Contact(
#             name="API Support",
#             email="support@example.com",
#             url="https://www.example.com/support"
#         ),
#         license=openapi.License(
#             name="MIT License",
#             url="https://opensource.org/licenses/MIT"
#         ),
#     ),
#     public=True,
#     permission_classes=[permissions.AllowAny],
#     authentication_classes=[],
# )

# Main URL patterns
urlpatterns = [
    # ==================== ADMIN PANEL ====================
    path(settings.ADMIN_URL, admin.site.urls),

    # ==================== SEO FILES ====================
    path('robots.txt', robots_txt, name='robots-txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap-xml'),
    
    # ==================== API ROOT ====================
    path('', api_root, name='api-root'),
    
    # ==================== HEALTH CHECK ====================
    path('health/', health_check, name='health-check'),
    path('api/health/', health_check, name='api-health-check'),
    
    # ==================== API DOCUMENTATION ====================
    # Swagger UI - interaktiv dokumentatsiya
    # path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # modern-drf-swagger docs
    path('api/docs/', include('modern_drf_swagger.urls')),
    
    # ReDoc - chiroyli dokumentatsiya
    # path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # OpenAPI JSON/YAML - dasturiy ishlatish uchun
    # path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json-yaml'),
    
    # ==================== JWT AUTHENTICATION ====================
    path('api/auth/', include([
        # Token olish (login)
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        
        # Token yangilash (refresh token bilan yangi access token olish)
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        
        # Token tekshirish (token hali ishlaydimi?)
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
        
        # Token o'chirish (logout)
        path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    ])),
    
    # ==================== API ENDPOINTS V1 ====================
    path('api/v1/', include([
        # Accounts app (User boshqaruvi)
        path('accounts/', include('apps.account.urls', namespace='account')),
        
        # API app (Asosiy funksiyalar)
        path('', include('apps.api.urls', namespace='api')),
    ])),
    
    # ==================== DRF BROWSABLE API AUTH ====================
    # DRF ning o'zidagi login/logout sahifalari (development uchun qulay)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # ==================== INTERNATIONALIZATION ====================
    # Til almashtiruv
    path('i18n/', include('django.conf.urls.i18n')),
]

# ==================== STATIC VA MEDIA FILES ====================
if settings.DEBUG:
    # Development muhitida static va media fayllarni serve qilish
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug Toolbar (development uchun)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]

else:
    # Production muhitida (nginx/apache orqali serve qilish tavsiya etiladi)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes': False,
        }),
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
            'show_indexes': False,
        }),
    ]

# ==================== CUSTOM ERROR HANDLERS ====================
# Bu handlerlar apps/core/views.py da yozilgan bo'lishi kerak

# handler400 = 'apps.core.views.bad_request'          # 400 - Bad Request
# handler403 = 'apps.core.views.permission_denied'    # 403 - Forbidden
# handler404 = 'apps.core.views.not_found'            # 404 - Not Found
# handler500 = 'apps.core.views.server_error'         # 500 - Internal Server Error

# ==================== ADMIN SITE CUSTOMIZATION ====================
admin.site.site_header = "Django REST API - Admin Panel"
admin.site.site_title = "Django REST API Admin"
admin.site.index_title = "Boshqaruv paneli"
admin.site.site_url = "/api/docs/"  # Admin paneldagi "View site" tugmasi
