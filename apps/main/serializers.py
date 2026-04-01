from rest_framework import serializers

from .models import (
    AboutUzbekistan,
    Destination,
    DestinationCategory,
    DestinationImage,
    FAQ,
    ImagesHomepage,
    Region,
    RouteGuide,
)


def normalize_text_value(value):
    if isinstance(value, memoryview):
        value = value.tobytes()

    if isinstance(value, bytearray):
        value = bytes(value)

    if isinstance(value, bytes):
        if value.startswith((b"\xff\xfe", b"\xfe\xff")):
            try:
                return value.decode("utf-16")
            except UnicodeDecodeError:
                pass

        for encoding in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                continue

        return value.decode("utf-8", errors="replace")

    return value


def serialize_file_field(file_field):
    if not file_field:
        return None

    try:
        return normalize_text_value(file_field.url)
    except Exception:
        return normalize_text_value(str(file_field))


class MultilingualField(serializers.Field):
    """
    ModelTranslation maydonlarini yagona ko'rinishda qaytaradi.
    """

    def __init__(self, source_field, *args, **kwargs):
        self.orig_source_field = source_field
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        if obj is None:
            return None

        fields = self.orig_source_field.split(".")
        for field in fields[:-1]:
            obj = getattr(obj, field, None)
            if obj is None:
                return None

        final_field = fields[-1]
        fallback_value = normalize_text_value(getattr(obj, final_field, None))
        return {
            "uz": normalize_text_value(getattr(obj, f"{final_field}_uz", fallback_value)),
            "ru": normalize_text_value(getattr(obj, f"{final_field}_ru", fallback_value)),
            "en": normalize_text_value(getattr(obj, f"{final_field}_en", fallback_value)),
        }


class RegionListSerializer(serializers.ModelSerializer):
    name = MultilingualField("name")
    info = MultilingualField("info")
    count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Region
        fields = ("id", "name", "info", "slug", "count")


class RegionPageSerializer(RegionListSerializer):
    featured_image = serializers.SerializerMethodField()

    class Meta(RegionListSerializer.Meta):
        fields = RegionListSerializer.Meta.fields + ("featured_image",)

    def get_featured_image(self, obj):
        destination = obj.destinations.filter(
            is_active=True,
            cover_image__isnull=False,
        ).exclude(cover_image="").order_by("-is_featured", "-average_rating", "name").first()
        if destination:
            return serialize_file_field(destination.cover_image)
        return None


class CategoryListSerializer(serializers.ModelSerializer):
    name = MultilingualField("name")
    count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = DestinationCategory
        fields = ("id", "name", "slug", "icon", "count")


class DestinationImageSerializer(serializers.ModelSerializer):
    alt_text = MultilingualField("alt_text")
    caption = MultilingualField("caption")

    class Meta:
        model = DestinationImage
        fields = ("id", "image", "alt_text", "caption", "is_cover", "sort_order")


class DestinationBaseSerializer(serializers.ModelSerializer):
    name = MultilingualField("name")

    class Meta:
        model = Destination
        fields = ("id", "name", "slug")


class DestinationRoutePlaceSerializer(serializers.ModelSerializer):
    name = MultilingualField("name")

    class Meta:
        model = Destination
        fields = ("id", "name", "slug", "cover_image")


class RouteGuideSerializer(serializers.ModelSerializer):
    title = MultilingualField("title")
    starting_point = MultilingualField("starting_point")
    route_description = MultilingualField("route_description")
    notes = MultilingualField("notes")
    transport_type_label = serializers.CharField(source="get_transport_type_display", read_only=True)
    destinations = DestinationRoutePlaceSerializer(many=True, read_only=True)

    class Meta:
        model = RouteGuide
        fields = (
            "id",
            "title",
            "transport_type",
            "transport_type_label",
            "starting_point",
            "route_description",
            "distance_km",
            "notes",
            "destinations",
        )


class RouteGuideListSerializer(serializers.ModelSerializer):
    title = MultilingualField("title")
    starting_point = MultilingualField("starting_point")
    transport_type_label = serializers.CharField(source="get_transport_type_display", read_only=True)
    destination = DestinationBaseSerializer(read_only=True)
    destinations_count = serializers.IntegerField(read_only=True, required=False)
    preview_image = serializers.SerializerMethodField()

    class Meta:
        model = RouteGuide
        fields = (
            "id",
            "title",
            "transport_type",
            "transport_type_label",
            "starting_point",
            "distance_km",
            "destination",
            "destinations_count",
            "preview_image",
        )

    def get_preview_image(self, obj):
        if obj.destination and obj.destination.cover_image:
            return serialize_file_field(obj.destination.cover_image)

        destination = obj.destinations.filter(
            is_active=True,
            cover_image__isnull=False,
        ).exclude(cover_image="").order_by("-is_featured", "-average_rating", "name").first()
        if destination:
            return serialize_file_field(destination.cover_image)
        return None


class RouteGuideDetailSerializer(RouteGuideSerializer):
    destination = serializers.SerializerMethodField()

    class Meta(RouteGuideSerializer.Meta):
        fields = RouteGuideSerializer.Meta.fields + ("destination",)

    def get_destination(self, obj):
        if not obj.destination:
            return None
        return DestinationCardSerializer(obj.destination, context=self.context).data


class FAQSerializer(serializers.ModelSerializer):
    question = MultilingualField("question")
    answer = MultilingualField("answer")
    destination = DestinationBaseSerializer(read_only=True)

    class Meta:
        model = FAQ
        fields = ("id", "question", "answer", "destination")


class DestinationCardSerializer(serializers.ModelSerializer):
    name = MultilingualField("name")
    short_description = MultilingualField("short_description")
    destination_type_label = serializers.CharField(source="get_destination_type_display", read_only=True)
    region = RegionListSerializer(read_only=True)
    categories = CategoryListSerializer(many=True, read_only=True)
    best_time_to_visit = MultilingualField("best_time_to_visit")

    class Meta:
        model = Destination
        fields = (
            "id",
            "name",
            "slug",
            "destination_type",
            "destination_type_label",
            "short_description",
            "region",
            "categories",
            "cover_image",
            "hero_image",
            "average_rating",
            "best_time_to_visit",
            "google_maps_url",
            "yandex_maps_url",
        )


class DestinationDetailSerializer(serializers.ModelSerializer):
    name = MultilingualField("name")
    short_description = MultilingualField("short_description")
    overview = MultilingualField("overview")
    history = MultilingualField("history")
    visiting_hours = MultilingualField("visiting_hours")
    address = MultilingualField("address")
    best_time_to_visit = MultilingualField("best_time_to_visit")
    destination_type_label = serializers.CharField(source="get_destination_type_display", read_only=True)
    region = RegionListSerializer(read_only=True)
    categories = CategoryListSerializer(many=True, read_only=True)
    gallery = serializers.SerializerMethodField()
    nearby_places = DestinationCardSerializer(many=True, read_only=True)
    routes = serializers.SerializerMethodField()
    faqs_preview = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = (
            "id",
            "name",
            "slug",
            "destination_type",
            "destination_type_label",
            "short_description",
            "overview",
            "history",
            "visiting_hours",
            "address",
            "latitude",
            "longitude",
            "best_time_to_visit",
            "contact_phone",
            "google_maps_url",
            "yandex_maps_url",
            "hero_image",
            "cover_image",
            "average_rating",
            "region",
            "categories",
            "gallery",
            "nearby_places",
            "routes",
            "faqs_preview",
        )

    def get_gallery(self, obj):
        images = obj.gallery.all().order_by("sort_order", "created_at")
        return DestinationImageSerializer(images, many=True, context=self.context).data

    def get_routes(self, obj):
        routes = obj.route_guides.filter(is_active=True).order_by("sort_order", "title")
        return RouteGuideSerializer(routes, many=True, context=self.context).data

    def get_faqs_preview(self, obj):
        faqs = obj.faqs.filter(is_active=True).order_by("sort_order", "question")[:5]
        return FAQSerializer(faqs, many=True, context=self.context).data


class DestinationMapSerializer(serializers.ModelSerializer):
    name = MultilingualField("name")
    destination_type_label = serializers.CharField(source="get_destination_type_display", read_only=True)
    region_name = MultilingualField("region.name")

    class Meta:
        model = Destination
        fields = (
            "id",
            "name",
            "slug",
            "destination_type",
            "destination_type_label",
            "latitude",
            "longitude",
            "region_name",
            "cover_image",
            "google_maps_url",
        )


class SearchSuggestionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    name = MultilingualField("name")
    region_name = MultilingualField("region.name")

    class Meta:
        model = Destination
        fields = ("type", "id", "name", "slug", "destination_type", "region_name", "cover_image")

    def get_type(self, obj):
        return "destination"


class ImagesHomepageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagesHomepage
        fields = ("id", "image")


class AboutUzbekistanSerializer(serializers.ModelSerializer):
    title = MultilingualField("title")
    description = MultilingualField("description")
    images = ImagesHomepageSerializer(many=True, read_only=True)

    class Meta:
        model = AboutUzbekistan
        fields = ("title", "description", "images")
