import math

from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Prefetch, Q, Value, When
from django.shortcuts import get_object_or_404
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AboutUzbekistan, AboutUzbekistanVideo, CultureItem, Destination, DestinationCategory, FAQ, HomeBanner, Region, RouteGuide, SocialMedia
from .serializers import (
    AboutUzbekistanSerializer,
    CultureItemSerializer,
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
    SocialMediaSerializer,
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
REGION_SEARCH_FIELDS = (
    "name",
    "name_uz",
    "name_ru",
    "name_en",
    "info",
    "info_uz",
    "info_ru",
    "info_en",
)

CACHE_TTL_SEARCH_SECONDS = 60 * 5


def normalize_search_query(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def pick_localized_dict_value(value, lang: str) -> str:
    if isinstance(value, dict):
        return value.get(lang) or value.get("uz") or value.get("en") or ""
    return str(value or "")


def get_translated_value(obj, field: str, lang: str) -> str:
    localized_attr = f"{field}_{lang}"
    localized = getattr(obj, localized_attr, None)
    if localized:
        return str(localized)
    fallback = getattr(obj, field, "")
    return str(fallback or "")


def build_cache_key(prefix: str, *parts: str) -> str:
    normalized = [normalize_search_query(part) for part in parts]
    return f"{prefix}:" + ":".join(normalized)


def destination_relevance_expression(query_text: str):
    if not query_text:
        return Value(0, output_field=IntegerField())

    name_contains_query = (
        Q(name__icontains=query_text)
        | Q(name_uz__icontains=query_text)
        | Q(name_ru__icontains=query_text)
        | Q(name_en__icontains=query_text)
    )
    description_contains_query = (
        Q(short_description__icontains=query_text)
        | Q(short_description_uz__icontains=query_text)
        | Q(short_description_ru__icontains=query_text)
        | Q(short_description_en__icontains=query_text)
    )

    return (
        Case(When(slug__iexact=query_text, then=Value(140)), default=Value(0), output_field=IntegerField())
        + Case(When(name__iexact=query_text, then=Value(120)), default=Value(0), output_field=IntegerField())
        + Case(When(name__istartswith=query_text, then=Value(90)), default=Value(0), output_field=IntegerField())
        + Case(When(name_contains_query, then=Value(60)), default=Value(0), output_field=IntegerField())
        + Case(When(description_contains_query, then=Value(25)), default=Value(0), output_field=IntegerField())
        + Case(When(is_featured=True, then=Value(10)), default=Value(0), output_field=IntegerField())
    )


def route_relevance_expression(query_text: str):
    if not query_text:
        return Value(0, output_field=IntegerField())

    title_contains_query = (
        Q(title__icontains=query_text)
        | Q(title_uz__icontains=query_text)
        | Q(title_ru__icontains=query_text)
        | Q(title_en__icontains=query_text)
    )
    description_contains_query = (
        Q(route_description__icontains=query_text)
        | Q(route_description_uz__icontains=query_text)
        | Q(route_description_ru__icontains=query_text)
        | Q(route_description_en__icontains=query_text)
    )

    return (
        Case(When(title__iexact=query_text, then=Value(130)), default=Value(0), output_field=IntegerField())
        + Case(When(title__istartswith=query_text, then=Value(90)), default=Value(0), output_field=IntegerField())
        + Case(When(title_contains_query, then=Value(55)), default=Value(0), output_field=IntegerField())
        + Case(When(description_contains_query, then=Value(25)), default=Value(0), output_field=IntegerField())
        + Case(When(is_featured=True, then=Value(10)), default=Value(0), output_field=IntegerField())
    )


def region_relevance_expression(query_text: str):
    if not query_text:
        return Value(0, output_field=IntegerField())

    name_contains_query = (
        Q(name__icontains=query_text)
        | Q(name_uz__icontains=query_text)
        | Q(name_ru__icontains=query_text)
        | Q(name_en__icontains=query_text)
    )
    info_contains_query = (
        Q(info__icontains=query_text)
        | Q(info_uz__icontains=query_text)
        | Q(info_ru__icontains=query_text)
        | Q(info_en__icontains=query_text)
    )

    return (
        Case(When(slug__iexact=query_text, then=Value(130)), default=Value(0), output_field=IntegerField())
        + Case(When(name__iexact=query_text, then=Value(120)), default=Value(0), output_field=IntegerField())
        + Case(When(name__istartswith=query_text, then=Value(90)), default=Value(0), output_field=IntegerField())
        + Case(When(name_contains_query, then=Value(60)), default=Value(0), output_field=IntegerField())
        + Case(When(info_contains_query, then=Value(20)), default=Value(0), output_field=IntegerField())
        + Case(When(is_featured=True, then=Value(10)), default=Value(0), output_field=IntegerField())
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


def build_region_search_query(search_text):
    query = Q()
    for field in REGION_SEARCH_FIELDS:
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


def get_about_uzbekistan_data(request):
    video_queryset = AboutUzbekistanVideo.objects.filter(is_active=True).order_by("sort_order", "created_at")
    about_obj = AboutUzbekistan.objects.filter(is_active=True).prefetch_related(
        "images",
        Prefetch("videos", queryset=video_queryset),
    ).order_by(
        "sort_order", "created_at"
    ).first()
    if about_obj:
        return AboutUzbekistanSerializer(about_obj, context={"request": request}).data

    return {
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
        "video_url": "",
        "videos": [],
        "images": [],
    }


def _localized_map(obj, field_name: str):
    return {
        "uz": str(getattr(obj, f"{field_name}_uz", None) or getattr(obj, field_name, "") or ""),
        "ru": str(getattr(obj, f"{field_name}_ru", None) or getattr(obj, field_name, "") or ""),
        "en": str(getattr(obj, f"{field_name}_en", None) or getattr(obj, field_name, "") or ""),
    }


def get_home_banner_data(request):
    fallback_image_url = request.build_absolute_uri("/media/homepage/banner.jpg")
    default_payload = {
        "title": {
            "uz": "O'zbekistondagi eng mashhur turistik joylar va ziyoratgohlar",
            "ru": "The most popular tourist places and shrines in Uzbekistan",
            "en": "The most popular tourist spots and shrines in Uzbekistan",
        },
        "subtitle": {
            "uz": "Hududlar bo'yicha izlang, joy haqida o'qing va yo'nalishni toping.",
            "ru": "Search by regions, read about places and find routes.",
            "en": "Search by regions, read about the place and find the route.",
        },
        "featured_image": fallback_image_url,
        "featured_media": "",
        "cta_primary": {
            "label": {"uz": "Joylarni ko'rish", "ru": "View places", "en": "View places"},
            "url": "/places/",
        },
        "cta_secondary": {
            "label": {"uz": "Xaritada ko'rish", "ru": "View on map", "en": "View on map"},
            "url": "/map/",
        },
    }

    banner_obj = HomeBanner.objects.filter(is_active=True).order_by("-is_featured", "sort_order", "created_at").first()
    if not banner_obj:
        return default_payload

    image_url = fallback_image_url
    if banner_obj.featured_image:
        image_url = request.build_absolute_uri(banner_obj.featured_image.url)

    media_value = ""
    if banner_obj.media_file:
        media_value = request.build_absolute_uri(banner_obj.media_file.url)
    elif banner_obj.media_url:
        media_value = banner_obj.media_url

    return {
        "title": _localized_map(banner_obj, "title"),
        "subtitle": _localized_map(banner_obj, "subtitle"),
        "featured_image": image_url,
        "featured_media": media_value,
        "cta_primary": {
            "label": _localized_map(banner_obj, "cta_primary_label"),
            "url": banner_obj.cta_primary_url or "/places/",
        },
        "cta_secondary": {
            "label": _localized_map(banner_obj, "cta_secondary_label"),
            "url": banner_obj.cta_secondary_url or "/map/",
        },
    }


def get_culture_items_data(request, limit: int = 8):
    queryset = CultureItem.objects.filter(is_active=True).order_by(
        "-is_featured",
        "sort_order",
        "title",
    )
    if limit > 0:
        queryset = queryset[:limit]
    return CultureItemSerializer(queryset, many=True, context={"request": request}).data


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

        about_data = get_about_uzbekistan_data(request)
        banner_data = get_home_banner_data(request)

        stats_data = {
            "regions_count": Region.objects.filter(is_active=True).count(),
            "places_count": destination_qs.count(),
            "pilgrimage_count": destination_qs.filter(destination_type=Destination.DestinationType.PILGRIMAGE).count(),
            "tourist_count": destination_qs.filter(destination_type=Destination.DestinationType.TOURIST).count(),
        }

        social_media_obj = SocialMedia.objects.filter(is_active=True).first()
        social_media_data = SocialMediaSerializer(social_media_obj).data if social_media_obj else None

        return Response(
            {
                "banner": banner_data,
                "about_uzbekistan": about_data,
                "stats": stats_data,
                "popular_tourist_places": DestinationCardSerializer(tourists, many=True, context={"request": request}).data,
                "pilgrimage_places": DestinationCardSerializer(pilgrims, many=True, context={"request": request}).data,
                "recommended_routes": RouteGuideSerializer(routes, many=True, context={"request": request}).data,
                "nearby_tourist_objects": DestinationCardSerializer(nearby_places, many=True, context={"request": request}).data,
                "culture_items": get_culture_items_data(request, limit=8),
                "categories": CategoryListSerializer(categories, many=True, context={"request": request}).data,
                "regions": RegionListSerializer(regions, many=True, context={"request": request}).data,
                "social_media": social_media_data,
            }
        )


class AboutAPIView(APIView):
    """
    About bo'limi uchun alohida endpoint.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["About"],
        operation_id_base="about",
        summary="O'zbekiston haqida",
        description="About bo'limi uchun title, description, video va rasmlar.",
    )

    def get(self, request, *args, **kwargs):
        return Response({"about_uzbekistan": get_about_uzbekistan_data(request)})


class CultureListAPIView(APIView):
    """
    Madaniyat bo'limi kartochkalari.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Culture"],
        operation_id_base="culture_list",
        summary="Madaniyat ro'yxati",
        description="Madaniyat bo'limi uchun kartochkalar ro'yxati.",
        manual_parameters=[
            query_param("limit", "Natijalar soni (1-100). Standart: 24", schema_type="integer"),
        ],
    )

    def get(self, request, *args, **kwargs):
        limit_param = request.query_params.get("limit", "24")
        try:
            limit = max(1, min(100, int(limit_param)))
        except ValueError:
            limit = 24

        return Response({"results": get_culture_items_data(request, limit=limit)})


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
        query_text = normalize_search_query(request.query_params.get("q", ""))
        if not query_text:
            return Response({"query": query_text, "results": []})

        limit_param = request.query_params.get("limit", "10")
        try:
            limit = max(1, min(25, int(limit_param)))
        except ValueError:
            limit = 10

        cache_key = build_cache_key("search:suggestions", query_text, str(limit))
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        queryset = self.get_base_queryset().filter(build_search_query(query_text)).annotate(
            search_rank=destination_relevance_expression(query_text)
        ).order_by(
            "-search_rank",
            "-average_rating",
            "-is_featured",
            "name",
        )[:limit]

        serializer = SearchSuggestionSerializer(queryset, many=True, context={"request": request})
        payload = {"query": query_text, "results": serializer.data}
        cache.set(cache_key, payload, CACHE_TTL_SEARCH_SECONDS)
        return Response(payload)


class SearchGlobalAPIView(APIView):
    """
    Destination, route va region bo'yicha global qidiruv.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Search"],
        operation_id_base="search_global",
        summary="Global qidiruv",
        description="Destination, route va region bo'yicha relevance asosidagi global qidiruv.",
        manual_parameters=[
            query_param("q", "Qidiruv matni.", required=True),
            query_param("limit", "Har bir bo'lim uchun maksimal natija soni (1-30).", schema_type="integer"),
        ],
    )

    def get(self, request, *args, **kwargs):
        query_text = normalize_search_query(request.query_params.get("q", ""))
        if not query_text:
            return Response(
                {
                    "query": "",
                    "totals": {"destinations": 0, "routes": 0, "regions": 0, "all": 0},
                    "results": {"destinations": [], "routes": [], "regions": []},
                }
            )

        limit_param = request.query_params.get("limit", "8")
        try:
            limit = max(1, min(30, int(limit_param)))
        except ValueError:
            limit = 8

        cache_key = build_cache_key("search:global", query_text, str(limit))
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        destinations = Destination.objects.filter(
            is_active=True,
            region__is_active=True,
        ).select_related("region", "region__country").prefetch_related("categories").filter(
            build_search_query(query_text)
        ).annotate(
            search_rank=destination_relevance_expression(query_text)
        ).order_by(
            "-search_rank",
            "-average_rating",
            "-is_featured",
            "name",
        )[:limit]

        routes = RouteGuide.objects.filter(
            is_active=True,
            destination__is_active=True,
        ).select_related("destination", "destination__region").prefetch_related(
            "destinations",
            "destinations__region",
            "destinations__categories",
        ).filter(
            build_route_search_query(query_text)
        ).annotate(
            search_rank=route_relevance_expression(query_text),
            destinations_count=Count("destinations", distinct=True),
        ).order_by(
            "-search_rank",
            "-is_featured",
            "sort_order",
            "title",
        )[:limit]

        regions = Region.objects.filter(is_active=True).filter(
            build_region_search_query(query_text)
        ).annotate(
            search_rank=region_relevance_expression(query_text),
            count=Count(
                "destinations",
                filter=Q(destinations__is_active=True),
                distinct=True,
            ),
        ).order_by(
            "-search_rank",
            "-count",
            "sort_order",
            "name",
        )[:limit]

        destination_data = DestinationCardSerializer(destinations, many=True, context={"request": request}).data
        route_data = RouteGuideListSerializer(routes, many=True, context={"request": request}).data
        region_data = RegionListSerializer(regions, many=True, context={"request": request}).data

        payload = {
            "query": query_text,
            "totals": {
                "destinations": len(destination_data),
                "routes": len(route_data),
                "regions": len(region_data),
                "all": len(destination_data) + len(route_data) + len(region_data),
            },
            "results": {
                "destinations": destination_data,
                "routes": route_data,
                "regions": region_data,
            },
        }
        cache.set(cache_key, payload, CACHE_TTL_SEARCH_SECONDS)
        return Response(payload)


class SEOMetaAPIView(APIView):
    """
    Frontend uchun page-level SEO metadata endpointi.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["SEO"],
        operation_id_base="seo_meta",
        summary="SEO metadata",
        description="Berilgan page_type uchun meta, OG, Twitter va structured_data qaytaradi.",
        manual_parameters=[
            query_param("page_type", "home | about | culture | place | route | region | search", required=True),
            query_param("lang", "uz | ru | en (default: uz)"),
            query_param("slug", "place yoki region uchun slug"),
            query_param("id", "route uchun UUID"),
            query_param("q", "search page uchun qidiruv matni"),
        ],
    )

    def _build_payload(
        self,
        *,
        title: str,
        description: str,
        keywords: str,
        canonical_url: str,
        image_url: str,
        robots: str,
        structured_data: dict,
        page_type: str,
    ):
        return {
            "page_type": page_type,
            "title": title,
            "description": description,
            "keywords": keywords,
            "canonical_url": canonical_url,
            "robots": robots,
            "og": {
                "title": title,
                "description": description,
                "type": "website",
                "url": canonical_url,
                "image": image_url,
            },
            "twitter": {
                "card": "summary_large_image",
                "title": title,
                "description": description,
                "image": image_url,
            },
            "structured_data": structured_data,
        }

    def get(self, request, *args, **kwargs):
        page_type = normalize_search_query(request.query_params.get("page_type", "")).lower()
        lang = normalize_search_query(request.query_params.get("lang", "uz")).lower() or "uz"
        if lang not in {"uz", "ru", "en"}:
            lang = "uz"

        base_url = request.build_absolute_uri("/").rstrip("/")
        banner_data = get_home_banner_data(request)
        default_image = banner_data.get("featured_image") or request.build_absolute_uri("/media/homepage/banner.jpg")

        if page_type == "home":
            title = "UzTourism - O'zbekiston bo'ylab sayohat va ziyorat"
            description = "O'zbekistonning turistik joylari, ziyoratgohlari va marshrutlari bo'yicha to'liq qo'llanma."
            keywords = "uzbekistan tourism, travel uzbekistan, ziyorat, tour routes"
            canonical_url = f"{base_url}/"
            structured_data = {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": "UzTourism",
                "url": canonical_url,
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{base_url}/search?q={{search_term_string}}",
                    "query-input": "required name=search_term_string",
                },
            }
            return Response(
                self._build_payload(
                    title=title,
                    description=description,
                    keywords=keywords,
                    canonical_url=canonical_url,
                    image_url=default_image,
                    robots="index,follow",
                    structured_data=structured_data,
                    page_type=page_type,
                )
            )

        if page_type == "about":
            about_data = get_about_uzbekistan_data(request)
            title_text = pick_localized_dict_value(about_data.get("title"), lang)
            desc_text = pick_localized_dict_value(about_data.get("description"), lang)
            about_images = about_data.get("images") or []
            image_url = about_images[0].get("image") if about_images else default_image
            about_videos = about_data.get("videos") or []
            video_urls = [item.get("url") for item in about_videos if isinstance(item, dict) and item.get("url")]
            if not video_urls and about_data.get("video_url"):
                # Backward compatibility: eski single maydon bo'lsa ham structured data ishlasin.
                video_urls = [about_data.get("video_url")]
            canonical_url = f"{base_url}/about/"
            structured_data = {
                "@context": "https://schema.org",
                "@type": "AboutPage",
                "name": title_text,
                "description": desc_text,
                "url": canonical_url,
            }
            if video_urls:
                video_objects = [
                    {
                        "@type": "VideoObject",
                        "name": f"{title_text} video {idx + 1}",
                        "description": desc_text,
                        "contentUrl": url,
                    }
                    for idx, url in enumerate(video_urls)
                ]
                structured_data["video"] = video_objects[0] if len(video_objects) == 1 else video_objects

            return Response(
                self._build_payload(
                    title=f"{title_text} | UzTourism",
                    description=desc_text,
                    keywords="about uzbekistan, uzbekistan tourism, uzbekistan travel guide",
                    canonical_url=canonical_url,
                    image_url=image_url,
                    robots="index,follow",
                    structured_data=structured_data,
                    page_type=page_type,
                )
            )

        if page_type == "culture":
            culture_items = get_culture_items_data(request, limit=8)
            canonical_url = f"{base_url}/culture/"
            title = "Madaniyat | UzTourism"
            description = "Milliy hunarmandchilik, an'analar va madaniy meros bo'yicha tanlangan kartochkalar."
            image_url = default_image
            if culture_items and isinstance(culture_items[0], dict):
                image_url = culture_items[0].get("image") or default_image

            structured_data = {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": title,
                "description": description,
                "url": canonical_url,
            }

            return Response(
                self._build_payload(
                    title=title,
                    description=description,
                    keywords="madaniyat, culture uzbekistan, handicraft, heritage",
                    canonical_url=canonical_url,
                    image_url=image_url,
                    robots="index,follow",
                    structured_data=structured_data,
                    page_type=page_type,
                )
            )

        if page_type == "place":
            slug = normalize_search_query(request.query_params.get("slug", ""))
            if not slug:
                return Response({"detail": "place uchun slug parametri majburiy."}, status=400)

            destination = get_object_or_404(
                Destination.objects.select_related("region", "region__country").prefetch_related("categories"),
                is_active=True,
                region__is_active=True,
                slug=slug,
            )
            name = get_translated_value(destination, "name", lang)
            summary = get_translated_value(destination, "short_description", lang)
            image_url = (
                request.build_absolute_uri(destination.hero_image.url)
                if destination.hero_image
                else request.build_absolute_uri(destination.cover_image.url)
                if destination.cover_image
                else default_image
            )
            category_keywords = ", ".join(destination.categories.values_list("slug", flat=True))
            canonical_url = f"{base_url}/places/{destination.slug}/"
            structured_data = {
                "@context": "https://schema.org",
                "@type": "TouristAttraction",
                "name": name,
                "description": summary,
                "url": canonical_url,
                "address": get_translated_value(destination, "address", lang),
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": float(destination.latitude) if destination.latitude is not None else None,
                    "longitude": float(destination.longitude) if destination.longitude is not None else None,
                },
            }

            return Response(
                self._build_payload(
                    title=f"{name} | UzTourism",
                    description=summary,
                    keywords=f"{name}, {category_keywords}, uzbekistan tourism",
                    canonical_url=canonical_url,
                    image_url=image_url,
                    robots="index,follow",
                    structured_data=structured_data,
                    page_type=page_type,
                )
            )

        if page_type == "region":
            slug = normalize_search_query(request.query_params.get("slug", ""))
            if not slug:
                return Response({"detail": "region uchun slug parametri majburiy."}, status=400)

            region = get_object_or_404(Region.objects.select_related("country"), is_active=True, slug=slug)
            name = get_translated_value(region, "name", lang)
            info = get_translated_value(region, "info", lang)
            featured_destination = region.destinations.filter(
                is_active=True,
                cover_image__isnull=False,
            ).exclude(cover_image="").order_by("-is_featured", "-average_rating", "name").first()
            image_url = request.build_absolute_uri(featured_destination.cover_image.url) if featured_destination else default_image
            canonical_url = f"{base_url}/regions/{region.slug}/"
            structured_data = {
                "@context": "https://schema.org",
                "@type": "Place",
                "name": name,
                "description": info,
                "url": canonical_url,
            }

            return Response(
                self._build_payload(
                    title=f"{name} viloyati | UzTourism",
                    description=info or f"{name} viloyatidagi turistik joylar va ziyoratgohlar.",
                    keywords=f"{name}, region uzbekistan, tourism",
                    canonical_url=canonical_url,
                    image_url=image_url,
                    robots="index,follow",
                    structured_data=structured_data,
                    page_type=page_type,
                )
            )

        if page_type == "route":
            route_id = normalize_search_query(request.query_params.get("id", ""))
            if not route_id:
                return Response({"detail": "route uchun id (UUID) parametri majburiy."}, status=400)

            route = get_object_or_404(
                RouteGuide.objects.select_related("destination", "destination__region"),
                is_active=True,
                destination__is_active=True,
                id=route_id,
            )
            title = get_translated_value(route, "title", lang)
            description = get_translated_value(route, "route_description", lang)
            image_url = (
                request.build_absolute_uri(route.destination.cover_image.url)
                if route.destination and route.destination.cover_image
                else default_image
            )
            canonical_url = f"{base_url}/routes/{route.id}/"
            structured_data = {
                "@context": "https://schema.org",
                "@type": "TouristTrip",
                "name": title,
                "description": description,
                "url": canonical_url,
            }

            return Response(
                self._build_payload(
                    title=f"{title} | UzTourism",
                    description=description,
                    keywords=f"{title}, route, travel uzbekistan",
                    canonical_url=canonical_url,
                    image_url=image_url,
                    robots="index,follow",
                    structured_data=structured_data,
                    page_type=page_type,
                )
            )

        if page_type == "search":
            query_text = normalize_search_query(request.query_params.get("q", ""))
            canonical_url = f"{base_url}/search/?q={query_text}"
            structured_data = {
                "@context": "https://schema.org",
                "@type": "SearchResultsPage",
                "name": f'"{query_text}" bo‘yicha qidiruv natijalari',
                "url": canonical_url,
            }
            return Response(
                self._build_payload(
                    title=f'"{query_text}" bo‘yicha natijalar | UzTourism',
                    description=f'"{query_text}" bo‘yicha qidiruv natijalari sahifasi.',
                    keywords=f"search, {query_text}, uzbekistan tourism",
                    canonical_url=canonical_url,
                    image_url=default_image,
                    robots="noindex,follow",
                    structured_data=structured_data,
                    page_type=page_type,
                )
            )

        return Response(
            {"detail": "Noto'g'ri page_type. Ruxsat etilganlari: home, about, culture, place, route, region, search"},
            status=400,
        )


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


class SocialMediaAPIView(APIView):
    """
    Ijtimoiy tarmoqlar (Social Media) ro'yxatini qaytaradi.
    """

    permission_classes = [AllowAny]
    schema = SwaggerAutoSchema(
        tags=["Meta"],
        operation_id_base="social_media",
        summary="Ijtimoiy tarmoqlar",
        description="Loyiha ijtimoiy tarmoq havolalarini qaytaradi.",
    )

    def get(self, request, *args, **kwargs):
        social_media_obj = SocialMedia.objects.filter(is_active=True).first()
        if social_media_obj:
            serializer = SocialMediaSerializer(social_media_obj)
            return Response(serializer.data)
        return Response({})

