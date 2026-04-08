import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def build_unique_slug(instance, value: str, field_name: str = "slug") -> str:
    base_slug = slugify(value)[:170] or uuid.uuid4().hex[:10]
    model_class = instance.__class__
    slug = base_slug
    counter = 2

    while model_class.objects.exclude(pk=instance.pk).filter(**{field_name: slug}).exists():
        suffix = f"-{counter}"
        slug = f"{base_slug[: 180 - len(suffix)]}{suffix}"
        counter += 1

    return slug


class UUIDTimeStampedModel(models.Model):
    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Yangilangan vaqt"), auto_now=True)

    class Meta:
        abstract = True
        verbose_name = _("Vaqt belgili model")
        verbose_name_plural = _("Vaqt belgili modellar")


# class 

class PublishableModel(models.Model):
    is_active = models.BooleanField(_("Faol"), default=True, db_index=True)
    is_featured = models.BooleanField(_("Tavsiya etilgan"), default=False, db_index=True)
    sort_order = models.PositiveIntegerField(_("Tartib raqami"), default=0)

    class Meta:
        abstract = True
        verbose_name = _("Nashr qilinadigan model")
        verbose_name_plural = _("Nashr qilinadigan modellar")


class Country(UUIDTimeStampedModel, PublishableModel):
    name = models.CharField(_("Nomi"), max_length=120, unique=True)
    iso_code = models.CharField(_("ISO kodi"), max_length=2, null=True, blank=True, unique=True)
    currency_code = models.CharField(_("Valyuta kodi"), max_length=3, null=True, blank=True, default="UZS")
    phone_code = models.CharField(_("Telefon kodi"), max_length=10, null=True, blank=True)
    flag_emoji = models.CharField(_("Bayroq emojisi"), max_length=8, null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Davlat")
        verbose_name_plural = _("Davlatlar")

    def __str__(self) -> str:
        return self.name


class Region(UUIDTimeStampedModel, PublishableModel):
    country = models.ForeignKey(
        Country,
        verbose_name=_("Davlat"),
        on_delete=models.CASCADE,
        related_name="regions",
    )
    name = models.CharField(_("Nomi"), max_length=120)
    info = models.TextField(_("Ma'lumot"), null=True, blank=True)
    slug = models.SlugField(_("Slug"), max_length=180, null=True, blank=True)

    class Meta:
        ordering = ["country__name", "name"]
        verbose_name = _("Hudud")
        verbose_name_plural = _("Hududlar")
        constraints = [
            models.UniqueConstraint(fields=["country", "slug"], name="unique_region_slug_per_country"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name}, {self.country.name}"


class DestinationCategory(UUIDTimeStampedModel, PublishableModel):
    name = models.CharField(_("Nomi"), max_length=80, unique=True)
    slug = models.SlugField(_("Slug"), max_length=120, null=True, blank=True, unique=True)
    icon = models.CharField(
        _("Ikona"),
        max_length=80,
        null=True, blank=True,
        help_text=_("UI badge'lari uchun ixtiyoriy ikona nomi."),
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Joy kategoriyasi")
        verbose_name_plural = _("Joy kategoriyalari")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


# class Amenity(UUIDTimeStampedModel, PublishableModel):
#     name = models.CharField(_("Nomi"), max_length=80, unique=True)
#     slug = models.SlugField(_("Slug"), max_length=120, null=True, blank=True, unique=True)
#     icon = models.CharField(_("Ikona"), max_length=80, null=True, blank=True)

#     class Meta:
#         ordering = ["name"]
#         verbose_name = _("Qulaylik")
#         verbose_name_plural = _("Qulayliklar")

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = build_unique_slug(self, self.name)
#         super().save(*args, **kwargs)

#     def __str__(self) -> str:
#         return self.name


class Destination(UUIDTimeStampedModel, PublishableModel):
    class DestinationType(models.TextChoices):
        TOURIST = "tourist", _("Turistik joy")
        PILGRIMAGE = "pilgrimage", _("Ziyoratgoh")
        MIXED = "mixed", _("Turistik va ziyorat")

    region = models.ForeignKey(
        Region,
        verbose_name=_("Hudud"),
        on_delete=models.PROTECT,
        related_name="destinations",
    )
    categories = models.ManyToManyField(
        DestinationCategory,
        verbose_name=_("Kategoriyalar"),
        blank=True,
        related_name="destinations",
    )
    # amenities = models.ManyToManyField(
    #     Amenity,
    #     verbose_name=_("Qulayliklar"),
    #     blank=True,
    #     related_name="destinations",
    # )
    nearby_places = models.ManyToManyField(
        "self",
        verbose_name=_("Yaqin joylar"),
        blank=True,
        symmetrical=False,
        related_name="recommended_by",
    )
    name = models.CharField(_("Nomi"), max_length=180)
    slug = models.SlugField(_("Slug"), max_length=180, unique=True, blank=True)
    destination_type = models.CharField(
        _("Joy turi"),
        max_length=20,
        choices=DestinationType.choices,
        default=DestinationType.TOURIST,
    )
    # tagline = models.CharField(_("Shior"), max_length=220, blank=True)
    short_description = models.TextField(_("Qisqa tavsif"))
    overview = models.TextField(_("Batafsil ma'lumot"), null=True, blank=True)
    history = models.TextField(_("Tarixi"), null=True, blank=True)
    # how_to_get_there = models.TextField(_("Qanday boriladi"), blank=True)
    visiting_hours = models.CharField(_("Ish vaqti"), max_length=160, null=True, blank=True)
    address = models.CharField(_("Manzil"), max_length=255, null=True, blank=True)
    # district = models.CharField(_("Tuman/Shahar"), max_length=120, null=True, blank=True)
    # landmark = models.CharField(_("Mo'ljal"), max_length=180, null=True, blank=True)
    latitude = models.DecimalField(
        _("Kenglik"),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("-90")), MaxValueValidator(Decimal("90"))],
    )
    longitude = models.DecimalField(
        _("Uzunlik"),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("-180")), MaxValueValidator(Decimal("180"))],
    )
    best_time_to_visit = models.CharField(_("Borish uchun eng yaxshi vaqt"), max_length=120, null=True, blank=True)
    # recommended_visit_duration = models.CharField(_("Tavsiya etilgan tashrif davomiyligi"), max_length=120, null=True, blank=True)
    # entry_fee = models.DecimalField(
    #     _("Kirish narxi"),
    #     max_digits=10,
    #     decimal_places=2,
    #     blank=True,
    #     null=True,
    #     validators=[MinValueValidator(0)],
    # )
    # ticket_notes = models.CharField(_("Chipta izohi"), max_length=255, blank=True)
    contact_phone = models.CharField(_("Bog'lanish telefoni"), max_length=30, blank=True)
    # official_website = models.URLField(_("Rasmiy sayt"), blank=True)
    google_maps_url = models.URLField(_("Google Maps havolasi"), blank=True)
    yandex_maps_url = models.URLField(_("Yandex Maps havolasi"), blank=True)
    hero_image = models.ImageField(_("Asosiy banner rasmi"), upload_to="destinations/heroes/", blank=True, null=True)
    cover_image = models.ImageField(_("Muqova rasmi"), upload_to="destinations/covers/", blank=True, null=True)
    average_rating = models.DecimalField(
        _("O'rtacha reyting"),
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    # review_count = models.PositiveIntegerField(_("Sharhlar soni"), default=0)

    class Meta:
        ordering = ["sort_order", "-is_featured", "name"]
        verbose_name = _("Joy")
        verbose_name_plural = _("Joylar")
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["region", "destination_type", "is_active", "is_featured"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class DestinationImage(UUIDTimeStampedModel):
    destination = models.ForeignKey(
        Destination,
        verbose_name=_("Joy"),
        on_delete=models.CASCADE,
        related_name="gallery",
    )
    image = models.ImageField(_("Rasm"), upload_to="destinations/gallery/")
    alt_text = models.CharField(_("Alt matn"), max_length=180, blank=True)
    caption = models.CharField(_("Sarlavha"), max_length=220, blank=True)
    is_cover = models.BooleanField(_("Muqova rasmi"), default=False)
    sort_order = models.PositiveIntegerField(_("Tartib raqami"), default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]
        verbose_name = _("Joy rasmi")
        verbose_name_plural = _("Joy rasmlari")

    def __str__(self) -> str:
        return f"{self.destination.name} image"


class RouteGuide(UUIDTimeStampedModel, PublishableModel):
    class TransportType(models.TextChoices):
        CAR = "car", _("Mashina")
        BUS = "bus", _("Avtobus")
        TRAIN = "train", _("Poyezd")
        TAXI = "taxi", _("Taksi")
        WALK = "walk", _("Piyoda")

    destination = models.ForeignKey(
        Destination,
        verbose_name=_("Joy"),
        on_delete=models.CASCADE,
        related_name="route_guides",
    )
    title = models.CharField(_("Sarlavha"), max_length=180)
    transport_type = models.CharField(
        _("Transport turi"),
        max_length=20,
        choices=TransportType.choices,
        default=TransportType.CAR,
    )
    starting_point = models.CharField(_("Boshlanish nuqtasi"), max_length=180, blank=True)
    route_description = models.TextField(_("Yo'nalish tavsifi"))
    destinations = models.ManyToManyField(
        Destination,
        verbose_name=_("Joylar"),
        related_name="included_in_routes",
    )
    distance_km = models.DecimalField(
        _("Masofa (km)"),
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    duration_text = models.CharField(_("Davomiyligi"), max_length=120, blank=True)
    # map_url = models.URLField(_("Yo'nalish havolasi"), blank=True)
    notes = models.TextField(_("Qo'shimcha izoh"), null=True, blank=True)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = _("Yo'nalish")
        verbose_name_plural = _("Yo'nalishlar")

    def __str__(self) -> str:
        return self.title


# class Review(UUIDTimeStampedModel, PublishableModel):
#     destination = models.ForeignKey(
#         Destination,
#         verbose_name=_("Joy"),
#         on_delete=models.CASCADE,
#         related_name="reviews",
#     )
#     author_name = models.CharField(_("Muallif ismi"), max_length=120)
#     author_email = models.EmailField(_("Muallif emaili"), blank=True)
#     rating = models.PositiveSmallIntegerField(
#         _("Baho"),
#         validators=[MinValueValidator(1), MaxValueValidator(5)],
#     )
#     title = models.CharField(_("Sarlavha"), max_length=160, blank=True)
#     body = models.TextField(_("Matn"))
#     visited_at = models.DateField(_("Tashrif sanasi"), blank=True, null=True)
#     is_approved = models.BooleanField(_("Tasdiqlangan"), default=False, db_index=True)

#     class Meta:
#         ordering = ["-created_at"]
#         verbose_name = _("Sharh")
#         verbose_name_plural = _("Sharhlar")
#         indexes = [
#             models.Index(fields=["destination", "is_approved"]),
#             models.Index(fields=["rating"]),
#         ]

#     def __str__(self) -> str:
#         return f"{self.author_name} - {self.rating}/5"


class FAQ(UUIDTimeStampedModel, PublishableModel):
    destination = models.ForeignKey(
        Destination,
        verbose_name=_("Joy"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="faqs",
    )
    question = models.CharField(_("Savol"), max_length=255)
    answer = models.TextField(_("Javob"))

    class Meta:
        ordering = ["sort_order", "question"]
        verbose_name = _("Savol-javob")
        verbose_name_plural = _("Savol-javoblar")

    def __str__(self) -> str:
        return self.question


class ImagesHomepage(UUIDTimeStampedModel):
    image = models.ImageField(_("Rasm"), upload_to="homepage/images/")
    

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("Bosh sahifa rasmi")
        verbose_name_plural = _("Bosh sahifa rasmlari")

    def __str__(self) -> str:
        return self.image.name

class AboutUzbekistan(UUIDTimeStampedModel, PublishableModel):
    title = models.CharField(_("Sarlavha"), max_length=180)
    description = models.TextField(_("Tavsif"))
    video_url = models.URLField(_("Video havolasi"), blank=True)
    images = models.ManyToManyField(ImagesHomepage, verbose_name=_("Rasmlar"), related_name="about_uzbekistan")


    class Meta:
        ordering = ["created_at", "title"]
        verbose_name = _("O'zbekiston haqida")
        verbose_name_plural = _("O'zbekiston haqida")

    def __str__(self) -> str:
        return self.title


class SocialMedia(UUIDTimeStampedModel, PublishableModel):
    instagram = models.URLField(_("Instagram"), blank=True)
    facebook = models.URLField(_("Facebook"), blank=True)
    youtube = models.URLField(_("YouTube"), blank=True)
    telegram = models.URLField(_("Telegram"), blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("Ijtimoiy tarmoq")
        verbose_name_plural = _("Ijtimoiy tarmoqlar")

    def __str__(self) -> str:
        return "Ijtimoiy tarmoq havolalari"
