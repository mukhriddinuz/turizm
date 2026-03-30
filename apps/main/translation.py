from modeltranslation.translator import register, TranslationOptions
from .models import (
    Country,
    Region,
    DestinationCategory,
    Destination,
    DestinationImage,
    RouteGuide,
    FAQ,
    AboutUzbekistan
)


@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Region)
class RegionTranslationOptions(TranslationOptions):
    fields = ('name', 'info')


@register(DestinationCategory)
class DestinationCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Destination)
class DestinationTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'short_description',
        'overview',
        'history',
        'visiting_hours',
        'address',
        'best_time_to_visit'
    )


@register(DestinationImage)
class DestinationImageTranslationOptions(TranslationOptions):
    fields = ('alt_text', 'caption')


@register(RouteGuide)
class RouteGuideTranslationOptions(TranslationOptions):
    fields = ('title', 'starting_point', 'route_description', 'notes')


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')


@register(AboutUzbekistan)
class AboutUzbekistanTranslationOptions(TranslationOptions):
    fields = ('title', 'description')
