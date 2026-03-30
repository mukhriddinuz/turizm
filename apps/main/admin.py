from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import (
    Country,
    Region,
    DestinationCategory,
    Destination,
    DestinationImage,
    RouteGuide,
    FAQ,
    ImagesHomepage,
    AboutUzbekistan
)


@admin.register(Country)
class CountryAdmin(TranslationAdmin):
    list_display = ('name', 'iso_code', 'currency_code', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(Region)
class RegionAdmin(TranslationAdmin):
    list_display = ('name', 'country', 'is_active')
    search_fields = ('name',)
    list_filter = ('country', 'is_active')


@admin.register(DestinationCategory)
class DestinationCategoryAdmin(TranslationAdmin):
    list_display = ('name', 'sort_order', 'is_active')
    search_fields = ('name',)


class DestinationImageInline(admin.TabularInline):
    model = DestinationImage
    extra = 1


@admin.register(Destination)
class DestinationAdmin(TranslationAdmin):
    list_display = ('name', 'region', 'destination_type', 'is_featured', 'is_active')
    list_filter = ('destination_type', 'region', 'is_featured', 'is_active')
    search_fields = ('name', 'short_description')
    inlines = [DestinationImageInline]


@admin.register(DestinationImage)
class DestinationImageAdmin(TranslationAdmin):
    list_display = ('destination', 'is_cover', 'sort_order')
    list_filter = ('is_cover',)


@admin.register(RouteGuide)
class RouteGuideAdmin(TranslationAdmin):
    list_display = ('title', 'destination', 'transport_type', 'is_active')
    list_filter = ('transport_type', 'is_active')
    search_fields = ('title',)


@admin.register(FAQ)
class FAQAdmin(TranslationAdmin):
    list_display = ('question', 'destination', 'is_active')
    search_fields = ('question',)


@admin.register(ImagesHomepage)
class ImagesHomepageAdmin(admin.ModelAdmin):
    pass


@admin.register(AboutUzbekistan)
class AboutUzbekistanAdmin(TranslationAdmin):
    list_display = ('title', 'is_active')
    search_fields = ('title',)
