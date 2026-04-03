import math

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AboutUzbekistan, Destination, DestinationCategory, FAQ, Region, RouteGuide
from .serializers import (
    AboutUzbekistanSerializer,
    CategoryListSerializer,
    DestinationBaseSerializer,
    DestinationCardSerializer,
    DestinationNearbySerializer,
    DestinationDetailSerializer,
    DestinationMapSerializer,
    FAQSerializer,
    RegionListSerializer,
    RegionPageSerializer,
    RouteGuideDetailSerializer,
    RouteGuideListSerializer,
    RouteGuideSerializer,
    SearchSuggestionSerializer,
)

SEARCH_FIELDS = (
    "name",
    "name_uz",
    "name_ru",
    "name_en",
    "short_description",
    "short_description_uz",
    "short_description_ru",
    "short_description_en",
)

ORDERING_FIELDS = {"name", "created_at", "average_rating", "sort_order"}
ROUTE_SEARCH_FIELDS = (
    "title",
    "title_uz",
    "title_ru",
    "title_en",
    "route_description",
    "route_description_uz",
    "route_description_ru",
    "route_description_en",
)


class SwaggerAutoSchema(AutoSchema):
    """
    drf-spectacular schema uchun qo'shimcha summary/description/params.
    """

    def __init__(
        self,
        *args,
        tags: list[str] | None = None,
        operation_id_base: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        manual_parameters: list[OpenApiParameter] | None = None,
        **kwargs,
    ):
        self._tags = tags or []
        self._operation_id_base = operation_id_base
        self._summary = summary
        self._description = description
        self._manual_parameters = manual_parameters or []
        super().__init__(*args, **kwargs)

    def get_tags(self):
        return self._tags or super().get_tags()

    def get_operation_id(self):
        return self._operation_id_base or super().get_operation_id()

    def get_summary(self):
        return self._summary or super().get_summary()

    def get_description(self):
        return self._description or super().get_description()

    def get_override_parameters(self):
        return [*super().get_override_parameters(), *self._manual_parameters]


def resolve_openapi_type(schema_type: str = "string", schema_format: str | None = None):
    if schema_format:
        if schema_format.lower() == "uuid":
            return OpenApiTypes.UUID

    type_map = {
        "string": OpenApiTypes.STR,
        "integer": OpenApiTypes.INT,
        "number": OpenApiTypes.NUMBER,
        "boolean": OpenApiTypes.BOOL,
    }
    return type_map.get(schema_type.lower(), OpenApiTypes.STR)


def query_param(
    name: str,
    description: str,
    schema_type: str = "string",
    required: bool = False,
    enum: list[str] | None = None,
):
    return OpenApiParameter(
        name=name,
        type=resolve_openapi_type(schema_type=schema_type),
        location=OpenApiParameter.QUERY,
        required=required,
        description=description,
        enum=enum,
    )


def path_param(name: str, description: str, schema_type: str = "string", schema_format: str | None = None):
    return OpenApiParameter(
        name=name,
        type=resolve_openapi_type(schema_type=schema_type, schema_format=schema_format),
        location=OpenApiParameter.PATH,
        required=True,
        description=description,
    )


def haversine(lat1, lon1, lat2, lon2):
    """
    Ikki koordinata orasidagi masofani KM da qaytaradi.
    """
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def parse_bool(value):
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return None


def build_search_query(search_text):
    query = Q()
    for field in SEARCH_FIELDS:
        query |= Q(**{f"{field}__icontains": search_text})
    return query


def apply_destination_filters(queryset, params):
    query_text = params.get("q", "").strip()
    region_slug = params.get("region", "").strip()
    category_slug = params.get("category", "").strip()
    destination_type = params.get("destination_type", "").strip()
    is_featured_raw = params.get("is_featured")

    if query_text:
        queryset = queryset.filter(build_search_query(query_text))

    if region_slug:
        queryset = queryset.filter(region__slug=region_slug)

    if category_slug:
        queryset = queryset.filter(categories__slug=category_slug)

    if destination_type in {choice[0] for choice in Destination.DestinationType.choices}:
        queryset = queryset.filter(destination_type=destination_type)

    is_featured = parse_bool(is_featured_raw)
    if is_featured is not None:
        queryset = queryset.filter(is_featured=is_featured)

    return queryset.distinct()


def build_route_search_query(search_text):
    query = Q()
    for field in ROUTE_SEARCH_FIELDS:
        query |= Q(**{f"{field}__icontains": search_text})
    return query


def apply_route_filters(queryset, params):
    query_text = params.get("q", "").strip()
    transport_type = params.get("transport_type", "").strip()
    destination_slug = params.get("destination_slug", "").strip()

    if query_text:
        queryset = queryset.filter(build_route_search_query(query_text))

    if transport_type in {choice[0] for choice in RouteGuide.TransportType.choices}:
        queryset = queryset.filter(transport_type=transport_type)

    if destination_slug:
        queryset = queryset.filter(Q(destination__slug=destination_slug) | Q(destinations__slug=destination_slug))

    return queryset.distinct()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class DestinationQuerysetMixin:
    def get_base_queryset(self):
        return Destination.objects.filter(
            is_active=True,
            region__is_active=True,
        ).select_related("region", "region__country").prefetch_related("categories")


class RouteGuideQuerysetMixin:
    def get_base_queryset(self):
        return RouteGuide.objects.filter(
            is_active=True,
            destination__is_active=True,
        ).select_related("destination", "destination__region").prefetch_related(
            "destinations",
            "destinations__region",
            "destinations__categories",
        )


DESTINATION_TYPE_ENUM = [choice[0] for choice in Destination.DestinationType.choices]
ROUTE_TYPE_ENUM = [choice[0] for choice in RouteGuide.TransportType.choices]

DESTINATION_FILTER_PARAMETERS = [
    query_param("q", "Joy nomi yoki tavsifi bo'yicha qidiruv."),
    query_param("region", "Viloyat slug bo'yicha filter."),
    query_param("category", "Kategoriya slug bo'yicha filter."),
    query_param("destination_type", "Joy turi bo'yicha filter.", enum=DESTINATION_TYPE_ENUM),
    query_param("is_featured", "Faqat tavsiya etilgan joylar.", schema_type="boolean"),
]

DESTINATION_LIST_PARAMETERS = DESTINATION_FILTER_PARAMETERS + [
    query_param("ordering", "Saralash: name, -created_at, -average_rating, sort_order."),
    query_param("page", "Sahifa raqami.", schema_type="integer"),
    query_param("page_size", "Sahifadagi elementlar soni.", schema_type="integer"),
]

ROUTE_LIST_PARAMETERS = [
    query_param("q", "Yo'nalish nomi yoki tavsifi bo'yicha qidiruv."),
    query_param("transport_type", "Transport turi bo'yicha filter.", enum=ROUTE_TYPE_ENUM),
    query_param("destination_slug", "Bog'liq joy slugi bo'yicha filter."),
    query_param("ordering", "Saralash: created_at, distance_km, sort_order, title."),
    query_param("page", "Sahifa raqami.", schema_type="integer"),
    query_param("page_size", "Sahifadagi elementlar soni.", schema_type="integer"),
]


class HomeAPIView(APIView):
    """
    Bosh sahifa uchun barcha bloklarni bitta endpointda qaytaradi.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Home"],
        operation_id_base="home",
        summary="Bosh sahifa ma'lumotlari",
        description="Banner, statistika, mashhur joylar, yo'nalishlar va meta bloklar.",
        manual_parameters=[
            query_param("lat", "Foydalanuvchi kenglik koordinatasi.", schema_type="number"),
            query_param("lng", "Foydalanuvchi uzunlik koordinatasi.", schema_type="number"),
        ],
    )

    def get(self, request, *args, **kwargs):
        destination_qs = Destination.objects.filter(
            is_active=True,
            region__is_active=True,
        ).select_related("region", "region__country").prefetch_related("categories")

        tourists = destination_qs.filter(destination_type=Destination.DestinationType.TOURIST).order_by(
            "-is_featured", "-average_rating", "name"
        )[:6]
        pilgrims = destination_qs.filter(destination_type=Destination.DestinationType.PILGRIMAGE).order_by(
            "-is_featured", "-average_rating", "name"
        )[:6]

        routes = RouteGuide.objects.filter(
            is_active=True,
            destination__is_active=True,
        ).select_related("destination").prefetch_related(
            "destinations",
            "destinations__region",
            "destinations__categories",
        ).order_by("sort_order", "title")[:3]

        categories = DestinationCategory.objects.filter(is_active=True).annotate(
            count=Count(
                "destinations",
                filter=Q(destinations__is_active=True),
                distinct=True,
            )
        ).order_by("-count", "sort_order", "name")

        regions = Region.objects.filter(is_active=True).annotate(
            count=Count(
                "destinations",
                filter=Q(destinations__is_active=True),
                distinct=True,
            )
        ).order_by("-count", "sort_order", "name")

        user_lat = request.query_params.get("lat")
        user_lng = request.query_params.get("lng")

        nearby_places = destination_qs.order_by("-is_featured", "-average_rating", "name")[:6]
        if user_lat and user_lng:
            try:
                user_lat_value = float(user_lat)
                user_lng_value = float(user_lng)
                places = [item for item in destination_qs if item.latitude is not None and item.longitude is not None]
                places.sort(
                    key=lambda item: haversine(
                        user_lat_value,
                        user_lng_value,
                        float(item.latitude),
                        float(item.longitude),
                    )
                )
                nearby_places = places[:6]
            except ValueError:
                nearby_places = destination_qs.order_by("-is_featured", "-average_rating", "name")[:6]

        about_obj = AboutUzbekistan.objects.filter(is_active=True).prefetch_related("images").order_by(
            "sort_order", "created_at"
        ).first()
        about_data = AboutUzbekistanSerializer(about_obj, context={"request": request}).data if about_obj else {
            "title": {
                "uz": "O'zbekiston haqida",
                "ru": "Об Узбекистане",
                "en": "About Uzbekistan",
            },
            "description": {
                "uz": "O'zbekiston qadimiy shaharlar, ziyoratgohlar va madaniy boyliklarga egadir",
                "ru": "Узбекистан обладает древними городами, святынями и богатым культурным наследием.",
                "en": "Uzbekistan has ancient cities, shrines, and rich cultural heritage.",
            },
            "images": [],
        }

        banner_data = {
            "title": {
                "uz": "O'zbekistondagi eng mashhur turistik joylar va ziyoratgohlar",
                "ru": "Самые популярные туристические места и святыни Узбекистана",
                "en": "The most popular tourist spots and shrines in Uzbekistan",
            },
            "subtitle": {
                "uz": "Hududlar bo'yicha izlang, joy haqida o'qing va yo'nalishni toping.",
                "ru": "Ищите по регионам, читайте о месте и находите маршрут.",
                "en": "Search by regions, read about the place and find the route.",
            },
            "featured_image": request.build_absolute_uri("/media/homepage/banner.jpg"),
            "cta_primary": {
                "label": {"uz": "Joylarni ko'rish", "ru": "Посмотреть места", "en": "View places"},
                "url": "/places/",
            },
            "cta_secondary": {
                "label": {"uz": "Xaritada ko'rish", "ru": "Посмотреть на карте", "en": "View on map"},
                "url": "/map/",
            },
        }

        stats_data = {
            "regions_count": Region.objects.filter(is_active=True).count(),
            "places_count": destination_qs.count(),
            "pilgrimage_count": destination_qs.filter(destination_type=Destination.DestinationType.PILGRIMAGE).count(),
            "tourist_count": destination_qs.filter(destination_type=Destination.DestinationType.TOURIST).count(),
        }

        return Response(
            {
                "banner": banner_data,
                "about_uzbekistan": about_data,
                "stats": stats_data,
                "popular_tourist_places": DestinationCardSerializer(tourists, many=True, context={"request": request}).data,
                "pilgrimage_places": DestinationCardSerializer(pilgrims, many=True, context={"request": request}).data,
                "recommended_routes": RouteGuideSerializer(routes, many=True, context={"request": request}).data,
                "nearby_tourist_objects": DestinationCardSerializer(nearby_places, many=True, context={"request": request}).data,
                "categories": CategoryListSerializer(categories, many=True, context={"request": request}).data,
                "regions": RegionListSerializer(regions, many=True, context={"request": request}).data,
            }
        )


class DestinationListAPIView(DestinationQuerysetMixin, generics.ListAPIView):
    """
    Joylar ro'yxati: filter, qidiruv, sort va pagination bilan.
    """

    permission_classes = [AllowAny]
    serializer_class = DestinationCardSerializer
    pagination_class = StandardResultsSetPagination
    schema = SwaggerAutoSchema(
        tags=["Destinations"],
        operation_id_base="destination_list",
        summary="Joylar ro'yxati",
        description="Turistik joylar ro'yxati: filter, qidiruv, tartiblash va pagination bilan.",
        manual_parameters=DESTINATION_LIST_PARAMETERS,
    )

    def get_queryset(self):
        queryset = apply_destination_filters(self.get_base_queryset(), self.request.query_params)

        ordering_param = self.request.query_params.get("ordering", "").strip()
        if ordering_param:
            order_fields = []
            for item in ordering_param.split(","):
                item = item.strip()
                if not item:
                    continue
                base_field = item.lstrip("-")
                if base_field in ORDERING_FIELDS:
                    order_fields.append(f"-{base_field}" if item.startswith("-") else base_field)
            if order_fields:
                return queryset.order_by(*order_fields)

        return queryset.order_by("-is_featured", "-average_rating", "sort_order", "name")


class NearbyPlacesAPIView(DestinationQuerysetMixin, APIView):
    """
    Foydalanuvchi turgan joydan ma'lum radiusdagi (km) joylarni qaytaradi.
    Sahifalanmasdan barcha topilgan joylar yuboriladi.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Destinations"],
        operation_id_base="places_nearby",
        summary="Yaqindagi joylar",
        description="Foydalanuvchi koordinatalari asosida belgilangan radiusdagi joylarni qaytaradi.",
        manual_parameters=[
            query_param("lat", "Foydalanuvchi kenglik koordinatasi.", schema_type="number", required=True),
            query_param("lng", "Foydalanuvchi uzunlik koordinatasi.", schema_type="number", required=True),
            query_param("radius", "Qidiruv radiusi (km). Standart: 10", schema_type="number"),
        ],
    )

    def get(self, request, *args, **kwargs):
        lat_param = request.query_params.get("lat")
        lng_param = request.query_params.get("lng")
        radius_param = request.query_params.get("radius", "10")

        if not lat_param or not lng_param:
            return Response({"error": "lat va lng parametrlari majburiy"}, status=400)

        try:
            user_lat = float(lat_param)
            user_lng = float(lng_param)
            radius = float(radius_param)
        except ValueError:
            return Response({"error": "Koordinatalar yoki radius noto'g'ri formatda"}, status=400)

        queryset = self.get_base_queryset().filter(
            latitude__isnull=False,
            longitude__isnull=False
        )

        nearby_places = []
        for item in queryset:
            dist = haversine(
                user_lat,
                user_lng,
                float(item.latitude),
                float(item.longitude),
            )
            if dist <= radius:
                item.distance_km = round(dist, 2)
                nearby_places.append(item)

        nearby_places.sort(key=lambda x: x.distance_km)

        serializer = DestinationNearbySerializer(nearby_places, many=True, context={"request": request})
        return Response({"results": serializer.data})


class RegionListAPIView(generics.ListAPIView):
    """
    Viloyatlar ro'yxati va har bir viloyatdagi joylar soni.
    """

    permission_classes = [AllowAny]
    serializer_class = RegionPageSerializer
    pagination_class = StandardResultsSetPagination
    schema = SwaggerAutoSchema(
        tags=["Regions"],
        operation_id_base="region_list",
        summary="Viloyatlar ro'yxati",
        description="Faol viloyatlar ro'yxatini joylar soni bilan qaytaradi.",
        manual_parameters=[
            query_param("page", "Sahifa raqami.", schema_type="integer"),
            query_param("page_size", "Sahifadagi elementlar soni.", schema_type="integer"),
        ],
    )

    def get_queryset(self):
        return Region.objects.filter(is_active=True).annotate(
            count=Count(
                "destinations",
                filter=Q(destinations__is_active=True),
                distinct=True,
            )
        ).order_by("-count", "sort_order", "name")


class RegionDetailAPIView(DestinationQuerysetMixin, APIView):
    """
    Bitta viloyat va unga tegishli joylar.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Regions"],
        operation_id_base="region_detail",
        summary="Viloyat detali",
        description="Bitta viloyat va unga tegishli joylar ro'yxati.",
        manual_parameters=[
            path_param("slug", "Viloyat slugi."),
            query_param("q", "Joy nomi yoki tavsifi bo'yicha qidiruv."),
            query_param("category", "Kategoriya slug bo'yicha filter."),
            query_param("destination_type", "Joy turi bo'yicha filter.", enum=DESTINATION_TYPE_ENUM),
            query_param("is_featured", "Faqat tavsiya etilgan joylar.", schema_type="boolean"),
            query_param("ordering", "Saralash: name, -created_at, -average_rating, sort_order."),
            query_param("page", "Sahifa raqami.", schema_type="integer"),
            query_param("page_size", "Sahifadagi elementlar soni.", schema_type="integer"),
        ],
    )

    def get(self, request, slug, *args, **kwargs):
        region = get_object_or_404(Region.objects.filter(is_active=True), slug=slug)
        places = apply_destination_filters(
            self.get_base_queryset().filter(region=region),
            request.query_params,
        ).order_by("-is_featured", "-average_rating", "sort_order", "name")

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(places, request, view=self)
        serialized_results = DestinationCardSerializer(page, many=True, context={"request": request}).data

        return Response(
            {
                "region": RegionListSerializer(region, context={"request": request}).data,
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serialized_results,
            }
        )


class DestinationDetailAPIView(generics.RetrieveAPIView):
    """
    Joyning to'liq ma'lumotlari: gallery, nearby, routes va FAQ preview.
    """

    permission_classes = [AllowAny]
    serializer_class = DestinationDetailSerializer
    lookup_field = "slug"
    schema = SwaggerAutoSchema(
        tags=["Destinations"],
        operation_id_base="destination_detail",
        summary="Joy detali",
        description="Bitta joyning to'liq ma'lumotlari: gallery, nearby, routes va FAQ preview bilan.",
        manual_parameters=[path_param("slug", "Joy slugi.")],
    )

    def get_queryset(self):
        return Destination.objects.filter(
            is_active=True,
            region__is_active=True,
        ).select_related("region", "region__country").prefetch_related(
            "categories",
            "gallery",
            "nearby_places",
            "nearby_places__region",
            "nearby_places__categories",
            "route_guides",
            "route_guides__destinations",
            "route_guides__destinations__region",
            "route_guides__destinations__categories",
            "faqs",
        )


class DestinationRoutesAPIView(DestinationQuerysetMixin, APIView):
    """
    Bitta joyga tegishli marshrutlar ro'yxati.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Destinations"],
        operation_id_base="destination_routes",
        summary="Joy yo'nalishlari",
        description="Bitta joyga tegishli marshrutlar ro'yxati.",
        manual_parameters=[path_param("slug", "Joy slugi.")],
    )

    def get(self, request, slug, *args, **kwargs):
        destination = get_object_or_404(self.get_base_queryset(), slug=slug)
        routes = destination.route_guides.filter(is_active=True).prefetch_related(
            "destinations",
            "destinations__region",
            "destinations__categories",
        ).order_by("sort_order", "title")

        return Response(
            {
                "destination": DestinationBaseSerializer(destination, context={"request": request}).data,
                "results": RouteGuideSerializer(routes, many=True, context={"request": request}).data,
            }
        )


class RouteGuideListAPIView(RouteGuideQuerysetMixin, generics.ListAPIView):
    """
    Sayohat yo'nalishlari ro'yxati.
    """

    permission_classes = [AllowAny]
    serializer_class = RouteGuideListSerializer
    pagination_class = StandardResultsSetPagination
    schema = SwaggerAutoSchema(
        tags=["Routes"],
        operation_id_base="route_list",
        summary="Sayohat yo'nalishlari",
        description="Sayohat yo'nalishlari ro'yxati: qidiruv, transport turi bo'yicha filter va pagination.",
        manual_parameters=ROUTE_LIST_PARAMETERS,
    )

    def get_queryset(self):
        queryset = apply_route_filters(self.get_base_queryset(), self.request.query_params).annotate(
            destinations_count=Count("destinations", distinct=True)
        )

        ordering_param = self.request.query_params.get("ordering", "").strip()
        allowed_ordering = {"created_at", "distance_km", "sort_order", "title"}
        if ordering_param:
            order_fields = []
            for item in ordering_param.split(","):
                item = item.strip()
                if not item:
                    continue
                base_field = item.lstrip("-")
                if base_field in allowed_ordering:
                    order_fields.append(f"-{base_field}" if item.startswith("-") else base_field)
            if order_fields:
                return queryset.order_by(*order_fields)

        return queryset.order_by("-is_featured", "sort_order", "title")


class RouteGuideDetailAPIView(RouteGuideQuerysetMixin, generics.RetrieveAPIView):
    """
    Sayohat yo'nalishi detali.
    """

    permission_classes = [AllowAny]
    serializer_class = RouteGuideDetailSerializer
    lookup_field = "id"
    schema = SwaggerAutoSchema(
        tags=["Routes"],
        operation_id_base="route_detail",
        summary="Sayohat yo'nalishi detali",
        description="Bitta sayohat yo'nalishi haqida to'liq ma'lumot.",
        manual_parameters=[path_param("id", "Yo'nalish UUID identifikatori.", schema_format="uuid")],
    )

    def get_queryset(self):
        return self.get_base_queryset()


class MapDestinationAPIView(DestinationQuerysetMixin, APIView):
    """
    Xarita markerlari uchun yengil destination payload.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Map"],
        operation_id_base="map_places",
        summary="Xarita markerlari",
        description="Xarita uchun yengil destination marker ro'yxati.",
        manual_parameters=DESTINATION_FILTER_PARAMETERS,
    )

    def get(self, request, *args, **kwargs):
        queryset = apply_destination_filters(self.get_base_queryset(), request.query_params).filter(
            latitude__isnull=False,
            longitude__isnull=False,
        ).order_by("-is_featured", "-average_rating", "sort_order", "name")

        serializer = DestinationMapSerializer(queryset, many=True, context={"request": request})
        return Response({"results": serializer.data})


class FAQListAPIView(generics.ListAPIView):
    """
    FAQ ro'yxati: global yoki destination bo'yicha filter bilan.
    """

    permission_classes = [AllowAny]
    serializer_class = FAQSerializer
    pagination_class = StandardResultsSetPagination
    schema = SwaggerAutoSchema(
        tags=["FAQ"],
        operation_id_base="faq_list",
        summary="FAQ ro'yxati",
        description="Global FAQ yoki bitta joyga tegishli FAQ ro'yxati.",
        manual_parameters=[
            query_param("destination_slug", "Bitta joy bo'yicha FAQ filter."),
            query_param("page", "Sahifa raqami.", schema_type="integer"),
            query_param("page_size", "Sahifadagi elementlar soni.", schema_type="integer"),
        ],
    )

    def get_queryset(self):
        queryset = FAQ.objects.filter(is_active=True).select_related(
            "destination",
            "destination__region",
        ).order_by("sort_order", "question")

        destination_slug = self.request.query_params.get("destination_slug", "").strip()
        if destination_slug:
            queryset = queryset.filter(destination__slug=destination_slug, destination__is_active=True)

        return queryset


class SearchSuggestionAPIView(DestinationQuerysetMixin, APIView):
    """
    Header search uchun tezkor destination takliflari.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Search"],
        operation_id_base="search_suggestions",
        summary="Qidiruv takliflari",
        description="Header qidiruv uchun destination suggestion endpoint.",
        manual_parameters=[
            query_param("q", "Qidiruv matni."),
            query_param("limit", "Natijalar soni (1-25).", schema_type="integer"),
        ],
    )

    def get(self, request, *args, **kwargs):
        query_text = request.query_params.get("q", "").strip()
        if not query_text:
            return Response({"query": query_text, "results": []})

        limit_param = request.query_params.get("limit", "10")
        try:
            limit = max(1, min(25, int(limit_param)))
        except ValueError:
            limit = 10

        queryset = self.get_base_queryset().filter(build_search_query(query_text)).order_by(
            "-is_featured",
            "-average_rating",
            "name",
        )[:limit]

        serializer = SearchSuggestionSerializer(queryset, many=True, context={"request": request})
        return Response({"query": query_text, "results": serializer.data})


class FilterMetaAPIView(APIView):
    """
    Frontend filter paneli uchun region/category/type metadatalari.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Meta"],
        operation_id_base="meta_filters",
        summary="Filter metadata",
        description="Frontend filter paneli uchun destination type, region va category metadatalari.",
    )

    def get(self, request, *args, **kwargs):
        destination_qs = Destination.objects.filter(
            is_active=True,
            region__is_active=True,
        )

        destination_types = [
            {
                "value": value,
                "label": label,
                "count": destination_qs.filter(destination_type=value).count(),
            }
            for value, label in Destination.DestinationType.choices
        ]

        regions = Region.objects.filter(is_active=True).annotate(
            count=Count(
                "destinations",
                filter=Q(destinations__is_active=True),
                distinct=True,
            )
        ).filter(count__gt=0).order_by("-count", "sort_order", "name")

        categories = DestinationCategory.objects.filter(is_active=True).annotate(
            count=Count(
                "destinations",
                filter=Q(destinations__is_active=True),
                distinct=True,
            )
        ).filter(count__gt=0).order_by("-count", "sort_order", "name")

        return Response(
            {
                "destination_types": destination_types,
                "regions": RegionListSerializer(regions, many=True, context={"request": request}).data,
                "categories": CategoryListSerializer(categories, many=True, context={"request": request}).data,
            }
        )
