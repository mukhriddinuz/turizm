import math
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Region, Destination, DestinationCategory, RouteGuide, AboutUzbekistan
from .serializers import (
    DestinationCardSerializer,
    RegionListSerializer,
    CategoryListSerializer,
    RouteGuideSerializer,
    AboutUzbekistanSerializer
)

def haversine(lat1, lon1, lat2, lon2):
    """
    Kalkulyator formulasi: Ikkita yer yuzi koordinatalari oralig'idagi xaqiqiy masofani KM hisobida beradi.
    """
    R = 6371.0  # Yerning radiusi (KM)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class HomeAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # 1. BOSH SAHIFA BANNERI (Hujjat bo'yicha static dictionary orqali beramiz)
        banner_data = {
            "title": {"uz": "O'zbekistondagi eng mashhur turistik joylar va ziyoratgohlar", "ru": "Самые популярные туристические места и святыни Узбекистана", "en": "The most popular tourist spots and shrines in Uzbekistan"},
            "subtitle": {"uz": "Hududlar bo'yicha izlang, joy haqida o'qing va yo'nalishni toping.", "ru": "Ищите по регионам, читайте о месте и находите маршрут.", "en": "Search by regions, read about the place and find the route."},
            "featured_image": request.build_absolute_uri('/media/homepage/banner.jpg'),
            "cta_primary": {
                "label": {"uz": "Joylarni ko'rish", "ru": "Посмотреть места", "en": "View places"},
                "url": "/places/"
            },
            "cta_secondary": {
                "label": {"uz": "Xaritada ko'rish", "ru": "Посмотреть на карте", "en": "View on map"},
                "url": "/map/"
            }
        }

        # 2. ABOUT UZBEKISTAN
        about_obj = AboutUzbekistan.objects.first()
        about_data = AboutUzbekistanSerializer(about_obj).data if about_obj else {
            "title": {"uz": "O'zbekiston haqida", "ru": "Об Узбекистане", "en": "About Uzbekistan"},
            "description": {"uz": "O'zbekiston qadimiy shaharlar, ziyoratgohlar va madaniy boyliklarga egadir", "ru": "Узбекистан обладает древними городами, святынями...", "en": "Uzbekistan has ancient cities, shrines and cultural wealth..."}
        }

        # 3. STATISTIKALAR
        stats_data = {
            "regions_count": Region.objects.count(),
            "places_count": Destination.objects.count(),
            "pilgrimage_count": Destination.objects.filter(destination_type='pilgrimage').count(),
            "tourist_count": Destination.objects.filter(destination_type='tourist').count()
        }

        # 4. RO'YXATLAR VA MODELLAR
        tourists = Destination.objects.filter(destination_type='tourist').order_by('-average_rating')[:6]
        pilgrims = Destination.objects.filter(destination_type='pilgrimage').order_by('-average_rating')[:6]
        
        # Marshrutlar (RouteGuides) agar bulsa 3 ta gacha chiqamiz (Hozircha agar bo'lsa)
        routes = RouteGuide.objects.all()[:3]
        
        # Kategoriyalar va hududlar
        categories = DestinationCategory.objects.all()
        regions = Region.objects.all()

        # 5. ENG YAQIN JOYLAR (Nearby objects lat/lng bn topish)
        user_lat = request.query_params.get('lat')
        user_lng = request.query_params.get('lng')
        
        nearby_places_qs = Destination.objects.all()
        if user_lat and user_lng:
            try:
                u_lat, u_lng = float(user_lat), float(user_lng)
                places_list = list(nearby_places_qs)
                # Formula orqali userga qaysi destination yaqin ekanligini hisoblaymiz (sortlash uchun custom logic)
                places_list.sort(key=lambda d: haversine(u_lat, u_lng, d.latitude, d.longitude) if d.latitude and d.longitude else float('inf'))
                nearby_places_qs = places_list[:6]
            except ValueError:
                # Noto'g'ri koordinata kelsa shunchaki mashhurlarini uzatamiz
                nearby_places_qs = nearby_places_qs.order_by('-average_rating')[:6]
        else:
            nearby_places_qs = nearby_places_qs.order_by('-average_rating')[:6]


        # FINAL RESPONSE JAVOBI
        return Response({
            "banner": banner_data,
            "about_uzbekistan": about_data,
            "stats": stats_data,
            "popular_tourist_places": DestinationCardSerializer(tourists, many=True, context={'request': request}).data,
            "pilgrimage_places": DestinationCardSerializer(pilgrims, many=True, context={'request': request}).data,
            "recommended_routes": RouteGuideSerializer(routes, many=True, context={'request': request}).data,
            "nearby_tourist_objects": DestinationCardSerializer(nearby_places_qs, many=True, context={'request': request}).data,
            "categories": CategoryListSerializer(categories, many=True, context={'request': request}).data,
            "regions": RegionListSerializer(regions, many=True, context={'request': request}).data
        })
