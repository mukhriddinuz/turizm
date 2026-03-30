from rest_framework import serializers
from .models import (
    Country, Region, DestinationCategory, Destination,
    DestinationImage, RouteGuide, FAQ, AboutUzbekistan
)

class MultilingualField(serializers.Field):
    """
    Maxsus maydon: Barcha tillardagi ma'lumotlarni nested dict (uz, ru, en) ko'rinishida qaytaradi.
    """
    def __init__(self, source_field, *args, **kwargs):
        self.orig_source_field = source_field
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        if obj is None:
            return None
        
        # nested maydonlar (masalan: `region.name`) ni hal qilish:
        fields = self.orig_source_field.split('.')
        for field in fields[:-1]:
            obj = getattr(obj, field, None)
            if obj is None:
                return None
                
        final_field = fields[-1]
        
        try:
            return {
                "uz": getattr(obj, f"{final_field}_uz", getattr(obj, final_field, None)),
                "ru": getattr(obj, f"{final_field}_ru", getattr(obj, final_field, None)),
                "en": getattr(obj, f"{final_field}_en", getattr(obj, final_field, None)),
            }
        except AttributeError:
            return None


class RegionListSerializer(serializers.ModelSerializer):
    name = MultilingualField('name')
    info = MultilingualField('info')
    
    class Meta:
        model = Region
        fields = ('id', 'name', 'info', 'slug')


class CategoryListSerializer(serializers.ModelSerializer):
    name = MultilingualField('name')
    
    class Meta:
        model = DestinationCategory
        fields = ('id', 'name', 'slug', 'icon')


class DestinationImageSerializer(serializers.ModelSerializer):
    alt_text = MultilingualField('alt_text')
    caption = MultilingualField('caption')
    
    class Meta:
        model = DestinationImage
        fields = ('id', 'image', 'alt_text', 'caption', 'is_cover', 'sort_order')


class RouteGuideSerializer(serializers.ModelSerializer):
    title = MultilingualField('title')
    starting_point = MultilingualField('starting_point')
    route_description = MultilingualField('route_description')
    notes = MultilingualField('notes')
    transport_type_label = serializers.CharField(source='get_transport_type_display', read_only=True)
    
    class Meta:
        model = RouteGuide
        fields = (
            'id', 'title', 'transport_type', 'transport_type_label', 
            'starting_point', 'route_description', 'distance_km', 
            'notes'
        )


class FAQSerializer(serializers.ModelSerializer):
    question = MultilingualField('question')
    answer = MultilingualField('answer')
    
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'answer')


class DestinationCardSerializer(serializers.ModelSerializer):
    name = MultilingualField('name')
    short_description = MultilingualField('short_description')
    destination_type_label = serializers.CharField(source='get_destination_type_display', read_only=True)
    region = RegionListSerializer()
    categories = CategoryListSerializer(many=True)
    best_time_to_visit = MultilingualField('best_time_to_visit')
    
    class Meta:
        model = Destination
        fields = (
            'id', 'name', 'slug', 'destination_type', 'destination_type_label',
            'short_description', 'region', 'categories', 
            'cover_image', 'hero_image', 'average_rating', 'best_time_to_visit',
            'google_maps_url', 'yandex_maps_url'
        )


class DestinationDetailSerializer(serializers.ModelSerializer):
    name = MultilingualField('name')
    short_description = MultilingualField('short_description')
    overview = MultilingualField('overview')
    history = MultilingualField('history')
    visiting_hours = MultilingualField('visiting_hours')
    address = MultilingualField('address')
    best_time_to_visit = MultilingualField('best_time_to_visit')

    destination_type_label = serializers.CharField(source='get_destination_type_display', read_only=True)
    region = RegionListSerializer()
    categories = CategoryListSerializer(many=True)
    gallery = serializers.SerializerMethodField()
    nearby_places = DestinationCardSerializer(many=True)
    
    class Meta:
        model = Destination
        fields = (
            'id', 'name', 'slug', 'destination_type', 'destination_type_label',
            'short_description', 'overview', 'history', 'visiting_hours', 'address',
            'latitude', 'longitude', 'best_time_to_visit',
            'contact_phone', 'google_maps_url', 'yandex_maps_url',
            'hero_image', 'cover_image', 'average_rating', 
            'region', 'categories', 'gallery', 'nearby_places'
        )

    def get_gallery(self, obj):
        images = obj.gallery.all().order_by('sort_order')
        return DestinationImageSerializer(images, many=True).data


class DestinationMapSerializer(serializers.ModelSerializer):
    name = MultilingualField('name')
    destination_type_label = serializers.CharField(source='get_destination_type_display', read_only=True)
    region_name = MultilingualField('region.name')
    
    class Meta:
        model = Destination
        fields = (
            'id', 'name', 'slug', 'destination_type', 'destination_type_label',
            'latitude', 'longitude', 'region_name', 'cover_image', 'google_maps_url'
        )

class SearchSuggestionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    name = MultilingualField('name')
    region_name = MultilingualField('region.name')

    class Meta:
        model = Destination
        fields = (
            'type', 'id', 'name', 'slug', 'destination_type', 'region_name', 'cover_image'
        )

    def get_type(self, obj):
        return 'destination'

class AboutUzbekistanSerializer(serializers.ModelSerializer):
    title = MultilingualField('title')
    description = MultilingualField('description')

    class Meta:
        model = AboutUzbekistan
        fields = ('title', 'description')
