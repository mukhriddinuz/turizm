import hashlib
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from apps.main.models import (
    AboutUzbekistan,
    AboutUzbekistanVideo,
    Country,
    CultureItem,
    Destination,
    DestinationCategory,
    DestinationImage,
    FAQ,
    ImagesHomepage,
    Region,
    RouteGuide,
)


REGIONS = [
    ("tashkent-city", "Toshkent shahri"),
    ("tashkent-region", "Toshkent viloyati"),
    ("samarkand-region", "Samarqand viloyati"),
    ("bukhara-region", "Buxoro viloyati"),
    ("khorezm-region", "Xorazm viloyati"),
    ("fergana-region", "Fargona viloyati"),
    ("namangan-region", "Namangan viloyati"),
]


CATEGORIES = [
    ("historical", "Tarixiy obida", "landmark"),
    ("pilgrimage", "Ziyoratgoh", "mosque"),
    ("nature", "Tabiat", "trees"),
    ("city", "Shahar joyi", "map-pin"),
]


DESTINATIONS = [
    ("registon-maydoni", "samarkand-region", "tourist", "Registon maydoni", "39.6542", "66.9759", ["historical", "city"]),
    ("shohi-zinda", "samarkand-region", "pilgrimage", "Shohi Zinda", "39.6626", "66.9875", ["historical", "pilgrimage"]),
    ("imom-buxoriy-majmuasi", "samarkand-region", "pilgrimage", "Imom Buxoriy majmuasi", "39.7754", "66.9216", ["pilgrimage"]),
    ("ark-qalasi", "bukhara-region", "tourist", "Ark qalasi", "39.7778", "64.4117", ["historical"]),
    ("labi-hovuz", "bukhara-region", "tourist", "Labi Hovuz", "39.7761", "64.4189", ["historical", "city"]),
    ("ichan-qala", "khorezm-region", "tourist", "Ichan Qala", "41.3775", "60.3600", ["historical"]),
    ("amir-temur-xiyoboni", "tashkent-city", "tourist", "Amir Temur xiyoboni", "41.3111", "69.2797", ["city"]),
    ("hazrati-imom-majmuasi", "tashkent-city", "pilgrimage", "Hazrati Imom majmuasi", "41.3362", "69.2400", ["pilgrimage"]),
    ("toshkent-teleminorasi", "tashkent-city", "tourist", "Toshkent teleminorasi", "41.3468", "69.2868", ["city"]),
    ("chorvoq-suv-ombori", "tashkent-region", "tourist", "Chorvoq suv ombori", "41.6290", "70.0500", ["nature"]),
    ("xudoyorxon-ordasi", "fergana-region", "tourist", "Xudoyorxon ordasi", "40.5286", "70.9428", ["historical", "city"]),
    ("afsonalar-vodiysi", "namangan-region", "tourist", "Afsonalar vodiysi", "41.0012", "71.6726", ["nature", "city"]),
]


NEARBY = {
    "registon-maydoni": ["shohi-zinda", "imom-buxoriy-majmuasi"],
    "shohi-zinda": ["registon-maydoni"],
    "imom-buxoriy-majmuasi": ["registon-maydoni"],
    "ark-qalasi": ["labi-hovuz"],
    "labi-hovuz": ["ark-qalasi"],
    "ichan-qala": [],
    "amir-temur-xiyoboni": ["hazrati-imom-majmuasi", "toshkent-teleminorasi"],
    "hazrati-imom-majmuasi": ["amir-temur-xiyoboni"],
    "toshkent-teleminorasi": ["amir-temur-xiyoboni"],
    "chorvoq-suv-ombori": ["amir-temur-xiyoboni"],
    "xudoyorxon-ordasi": ["afsonalar-vodiysi"],
    "afsonalar-vodiysi": ["xudoyorxon-ordasi"],
}


ROUTES = [
    ("Samarqand tarixiy yonalishi", "car", "registon-maydoni", ["registon-maydoni", "shohi-zinda", "imom-buxoriy-majmuasi"], "36.5"),
    ("Buxoro klassik yonalishi", "car", "ark-qalasi", ["ark-qalasi", "labi-hovuz"], "18.0"),
    ("Toshkent city tour", "taxi", "amir-temur-xiyoboni", ["amir-temur-xiyoboni", "hazrati-imom-majmuasi", "toshkent-teleminorasi"], "22.4"),
]

ABOUT_VIDEOS = [
    ("Uzbekistan tourism intro", "https://www.youtube.com/watch?v=aqz-KE-bpKQ"),
    ("Samarkand travel guide", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("Bukhara heritage tour", "https://www.youtube.com/watch?v=9bZkp7q19f0"),
]

CULTURE_ITEMS = [
    ("Kulolchilik", "Kulolchilik san'ati va milliy idishlar an'anasi."),
    ("Gilamdo'zlik", "Qo'lda to'qilgan gilamlar va bezak uslublari."),
    ("Hunarmandchilik", "Mahalliy ustalar ishlari va qadimiy usullar."),
    ("O'zbek adrasi", "Atlas va adras matolarini tayyorlash madaniyati."),
    ("O'zbek palovi", "Milliy taom tayyorlash va dasturxon an'analari."),
    ("O'zbek to'yi", "To'y marosimlari va milliy urf-odatlar."),
    ("Qog'ozni san'atda ishlatish", "Qog'oz o'ymakorligi va amaliy san'at."),
    ("Amir Temur muzeyi", "Tarixiy merosni aks ettiruvchi muzey tajribasi."),
]


class Command(BaseCommand):
    help = "Frontend testlari uchun to'liq demo ma'lumotlarni yaratadi."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Mavjud ma'lumotlarni tozalab, seedni toza qayta yaratadi.")
        parser.add_argument("--refresh-images", action="store_true", help="Mavjud rasmlar bo'lsa ham qayta placeholder rasm yaratadi.")

    def handle(self, *args, **options):
        reset = options["reset"]
        refresh_images = options["refresh_images"]

        with transaction.atomic():
            if reset:
                self._reset()

            country = self._seed_country()
            regions = self._seed_regions(country)
            categories = self._seed_categories()
            destinations = self._seed_destinations(regions, categories, refresh_images)
            self._seed_nearby(destinations)
            self._seed_routes(destinations)
            self._seed_faq(destinations)
            self._seed_about(refresh_images)
            self._seed_culture(refresh_images)

        self.stdout.write(self.style.SUCCESS("Seed tayyor: frontend uchun demo data yaratildi."))
        self.stdout.write(self.style.SUCCESS("Run: python manage.py seed_frontend_data --reset"))

    def _reset(self):
        RouteGuide.objects.all().delete()
        FAQ.objects.all().delete()
        DestinationImage.objects.all().delete()
        CultureItem.objects.all().delete()
        AboutUzbekistanVideo.objects.all().delete()
        AboutUzbekistan.objects.all().delete()
        ImagesHomepage.objects.all().delete()
        Destination.objects.all().delete()
        DestinationCategory.objects.all().delete()
        Region.objects.all().delete()
        Country.objects.all().delete()

    def _seed_country(self):
        country, _ = Country.objects.update_or_create(
            iso_code="UZ",
            defaults={
                "name": "O'zbekiston",
                "name_uz": "O'zbekiston",
                "name_ru": "Uzbekistan",
                "name_en": "Uzbekistan",
                "currency_code": "UZS",
                "phone_code": "+998",
                "is_active": True,
                "is_featured": True,
                "sort_order": 1,
            },
        )
        return country

    def _seed_regions(self, country):
        items = {}
        for idx, (slug, name) in enumerate(REGIONS, start=1):
            region, _ = Region.objects.update_or_create(
                country=country,
                slug=slug,
                defaults={
                    "name": name,
                    "name_uz": name,
                    "name_ru": name,
                    "name_en": name,
                    "info": f"{name} haqida demo ma'lumot.",
                    "info_uz": f"{name} haqida demo ma'lumot.",
                    "info_ru": f"Demo information about {name}.",
                    "info_en": f"Demo information about {name}.",
                    "is_active": True,
                    "is_featured": idx <= 3,
                    "sort_order": idx,
                },
            )
            items[slug] = region
        return items

    def _seed_categories(self):
        items = {}
        for idx, (slug, name, icon) in enumerate(CATEGORIES, start=1):
            category, _ = DestinationCategory.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "name_uz": name,
                    "name_ru": name,
                    "name_en": name,
                    "icon": icon,
                    "is_active": True,
                    "sort_order": idx,
                },
            )
            items[slug] = category
        return items

    def _seed_destinations(self, regions, categories, refresh_images):
        items = {}
        for idx, (slug, region_slug, dest_type, name, lat, lng, category_slugs) in enumerate(DESTINATIONS, start=1):
            region = regions[region_slug]
            destination, _ = Destination.objects.update_or_create(
                slug=slug,
                defaults={
                    "region": region,
                    "name": name,
                    "name_uz": name,
                    "name_ru": name,
                    "name_en": name,
                    "destination_type": dest_type,
                    "short_description": f"{name} - frontend test uchun demo joy.",
                    "short_description_uz": f"{name} - frontend test uchun demo joy.",
                    "short_description_ru": f"{name} - demo location for frontend tests.",
                    "short_description_en": f"{name} - demo location for frontend tests.",
                    "overview": f"{name} haqida qisqacha ma'lumot.",
                    "overview_uz": f"{name} haqida qisqacha ma'lumot.",
                    "overview_ru": f"Short overview for {name}.",
                    "overview_en": f"Short overview for {name}.",
                    "history": f"{name} tarixiga oid demo matn.",
                    "history_uz": f"{name} tarixiga oid demo matn.",
                    "history_ru": f"Demo history text for {name}.",
                    "history_en": f"Demo history text for {name}.",
                    "best_time_to_visit": "Aprel-Oktyabr",
                    "best_time_to_visit_uz": "Aprel-Oktyabr",
                    "best_time_to_visit_ru": "April-October",
                    "best_time_to_visit_en": "April-October",
                    "visiting_hours": "09:00-19:00",
                    "visiting_hours_uz": "09:00-19:00",
                    "visiting_hours_ru": "09:00-19:00",
                    "visiting_hours_en": "09:00-19:00",
                    "address": f"{region.name}, {name}",
                    "address_uz": f"{region.name}, {name}",
                    "address_ru": f"{region.name}, {name}",
                    "address_en": f"{region.name}, {name}",
                    "latitude": Decimal(lat),
                    "longitude": Decimal(lng),
                    "average_rating": Decimal("4.50") + Decimal((idx % 5) * 0.1),
                    "contact_phone": "+998901234567",
                    "google_maps_url": f"https://maps.google.com/?q={lat},{lng}",
                    "yandex_maps_url": f"https://yandex.uz/maps/?ll={lng},{lat}",
                    "is_active": True,
                    "is_featured": idx <= 6,
                    "sort_order": idx,
                },
            )
            destination.categories.set([categories[s] for s in category_slugs])
            self._ensure_destination_images(destination, refresh_images)
            self._ensure_gallery(destination, refresh_images)
            items[slug] = destination
        return items

    def _seed_nearby(self, destinations):
        for slug, nearby_slugs in NEARBY.items():
            destination = destinations.get(slug)
            if not destination:
                continue
            destination.nearby_places.set([destinations[s] for s in nearby_slugs if s in destinations])

    def _seed_routes(self, destinations):
        for idx, (title, transport, main_slug, route_slugs, distance) in enumerate(ROUTES, start=1):
            main_destination = destinations.get(main_slug)
            if not main_destination:
                continue

            route, _ = RouteGuide.objects.update_or_create(
                destination=main_destination,
                title_uz=title,
                defaults={
                    "title": title,
                    "title_ru": title,
                    "title_en": title,
                    "transport_type": transport,
                    "starting_point": main_destination.name,
                    "starting_point_uz": main_destination.name,
                    "starting_point_ru": main_destination.name,
                    "starting_point_en": main_destination.name,
                    "route_description": f"{title} bo'yicha demo marshrut tavsifi.",
                    "route_description_uz": f"{title} bo'yicha demo marshrut tavsifi.",
                    "route_description_ru": f"Demo route description for {title}.",
                    "route_description_en": f"Demo route description for {title}.",
                    "distance_km": Decimal(distance),
                    "notes": "Demo route note.",
                    "notes_uz": "Demo route note.",
                    "notes_ru": "Demo route note.",
                    "notes_en": "Demo route note.",
                    "is_active": True,
                    "is_featured": idx <= 2,
                    "sort_order": idx,
                },
            )
            route.destinations.set([destinations[s] for s in route_slugs if s in destinations])

    def _seed_faq(self, destinations):
        questions = [
            ("Bu joyga kirish pullikmi?", "Kirish shartlari mavsumga qarab o'zgarishi mumkin."),
            ("Qaysi vaqtda borish maqsadga muvofiq?", "Ertalab yoki kechki payt tashrif buyurish tavsiya etiladi."),
        ]
        for destination in destinations.values():
            for idx, (question, answer) in enumerate(questions, start=1):
                FAQ.objects.update_or_create(
                    destination=destination,
                    question_uz=question,
                    defaults={
                        "question": question,
                        "question_ru": question,
                        "question_en": question,
                        "answer": answer,
                        "answer_uz": answer,
                        "answer_ru": answer,
                        "answer_en": answer,
                        "is_active": True,
                        "sort_order": idx,
                    },
                )

    def _seed_about(self, refresh_images):
        images = list(ImagesHomepage.objects.order_by("created_at")[:3])
        while len(images) < 3:
            images.append(ImagesHomepage.objects.create())

        for idx, image_obj in enumerate(images, start=1):
            if refresh_images or not image_obj.image:
                content = self._placeholder_image(f"UzTourism Home {idx}", (1280, 720), f"home-{idx}")
                image_obj.image.save(f"home_about_{idx}.jpg", content, save=True)

        about = AboutUzbekistan.objects.order_by("created_at").first()
        if not about:
            about = AboutUzbekistan()
        about.title = "O'zbekiston haqida"
        about.title_uz = "O'zbekiston haqida"
        about.title_ru = "About Uzbekistan"
        about.title_en = "About Uzbekistan"
        about.description = "O'zbekiston turizm testlari uchun demo ma'lumotlar to'plami."
        about.description_uz = "O'zbekiston turizm testlari uchun demo ma'lumotlar to'plami."
        about.description_ru = "Demo dataset for Uzbekistan tourism frontend tests."
        about.description_en = "Demo dataset for Uzbekistan tourism frontend tests."
        about.video_url = ABOUT_VIDEOS[0][1]
        about.is_active = True
        about.is_featured = True
        about.sort_order = 1
        about.save()
        about.images.set(images)

        valid_orders = []
        for idx, (title, url) in enumerate(ABOUT_VIDEOS, start=1):
            AboutUzbekistanVideo.objects.update_or_create(
                about=about,
                sort_order=idx,
                defaults={
                    "title": title,
                    "url": url,
                    "is_active": True,
                    "is_featured": idx == 1,
                },
            )
            valid_orders.append(idx)

        about.videos.exclude(sort_order__in=valid_orders).delete()

    def _seed_culture(self, refresh_images):
        active_slugs = []
        for idx, (title, description) in enumerate(CULTURE_ITEMS, start=1):
            slug = slugify(title) or f"culture-{idx}"
            item, _ = CultureItem.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "title_uz": title,
                    "title_ru": title,
                    "title_en": title,
                    "short_description": description,
                    "short_description_uz": description,
                    "short_description_ru": description,
                    "short_description_en": description,
                    "detail_url": f"/culture/{slug}/",
                    "is_active": True,
                    "is_featured": idx <= 4,
                    "sort_order": idx,
                },
            )
            if refresh_images or not item.image:
                image = self._placeholder_image(f"{title}", (900, 1200), f"culture-{slug}")
                item.image.save(f"culture_{slug}.jpg", image, save=False)
                item.save(update_fields=["image"])
            active_slugs.append(slug)

        CultureItem.objects.exclude(slug__in=active_slugs).delete()

    def _ensure_destination_images(self, destination, refresh_images):
        changed = False
        if refresh_images or not destination.cover_image:
            cover = self._placeholder_image(f"{destination.name} Cover", (960, 640), f"cover-{destination.slug}")
            destination.cover_image.save(f"{destination.slug}_cover.jpg", cover, save=False)
            changed = True
        if refresh_images or not destination.hero_image:
            hero = self._placeholder_image(f"{destination.name} Hero", (1440, 800), f"hero-{destination.slug}")
            destination.hero_image.save(f"{destination.slug}_hero.jpg", hero, save=False)
            changed = True
        if changed:
            destination.save(update_fields=["cover_image", "hero_image"])

    def _ensure_gallery(self, destination, refresh_images):
        for idx in range(1, 4):
            gallery, _ = DestinationImage.objects.get_or_create(destination=destination, sort_order=idx)
            gallery.alt_text = f"{destination.name} gallery {idx}"
            gallery.alt_text_uz = gallery.alt_text
            gallery.alt_text_ru = gallery.alt_text
            gallery.alt_text_en = gallery.alt_text
            gallery.caption = f"{destination.name} photo {idx}"
            gallery.caption_uz = gallery.caption
            gallery.caption_ru = gallery.caption
            gallery.caption_en = gallery.caption
            gallery.is_cover = idx == 1
            if refresh_images or not gallery.image:
                image = self._placeholder_image(f"{destination.name} #{idx}", (1200, 800), f"gallery-{destination.slug}-{idx}")
                gallery.image.save(f"{destination.slug}_gallery_{idx}.jpg", image, save=False)
            gallery.save()

    def _placeholder_image(self, title, size, seed):
        color = self._pick_color(seed)
        image = Image.new("RGB", size, color)
        draw = ImageDraw.Draw(image)
        draw.rectangle([(0, int(size[1] * 0.65)), (size[0], size[1])], fill=tuple(max(0, c - 35) for c in color))

        try:
            title_font = ImageFont.truetype("arial.ttf", max(20, size[0] // 26))
            sub_font = ImageFont.truetype("arial.ttf", max(14, size[0] // 40))
        except OSError:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        draw.text((30, size[1] - 120), title[:45], fill="white", font=title_font)
        draw.text((30, size[1] - 80), "Demo frontend seed data", fill="white", font=sub_font)

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)
        return ContentFile(buffer.read())

    def _pick_color(self, seed):
        digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
        return (
            50 + (int(digest[0:2], 16) % 140),
            50 + (int(digest[2:4], 16) % 140),
            50 + (int(digest[4:6], 16) % 140),
        )
