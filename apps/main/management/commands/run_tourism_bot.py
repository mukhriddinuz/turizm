import asyncio
import math
import os
import random

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from apps.main.models import CultureItem, Destination

try:
    from aiogram import Bot, Dispatcher, F
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.filters import Command as TgCommand, CommandStart
    from aiogram.types import BufferedInputFile, InlineKeyboardButton, KeyboardButton, Message
    from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
except ImportError:  # pragma: no cover
    Bot = None
    Dispatcher = None


MENU_PLACES = "Joylar"
MENU_PILGRIMAGE = "Ziyoratgohlar"
MENU_RECREATION = "Dam olish maskanlari"
MENU_MUSEUMS = "Muzeylar"
MENU_FOOD = "Ovqatlanish"
MENU_CRAFTS = "Hunarmandchilik"
MENU_RANDOM = "Random joy"
MENU_NEARBY = "Yaqin joylar"
MENU_SEND_LOCATION = "Lokatsiyani yuborish"
MENU_BACK = "Menyuga qaytish"
LOCATION_PROMPT = "Yaqin joylarni topish uchun pastdagi tugmadan lokatsiyangizni yuboring."


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def build_main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text=MENU_PLACES)
    kb.button(text=MENU_PILGRIMAGE)
    kb.button(text=MENU_RECREATION)
    kb.button(text=MENU_MUSEUMS)
    kb.button(text=MENU_FOOD)
    kb.button(text=MENU_CRAFTS)
    kb.button(text=MENU_RANDOM)
    kb.button(text=MENU_NEARBY)
    kb.adjust(2, 2, 2, 2)
    return kb.as_markup(resize_keyboard=True)


def build_location_menu():
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text=MENU_SEND_LOCATION, request_location=True))
    kb.row(KeyboardButton(text=MENU_BACK))
    return kb.as_markup(resize_keyboard=True)


def build_place_inline(map_url: str | None):
    kb = InlineKeyboardBuilder()
    if map_url:
        kb.row(InlineKeyboardButton(text="Xaritada ochish", url=map_url))
    return kb.as_markup()


def make_caption(destination: Destination) -> str:
    name = destination.name or "Joy"
    region_name = destination.region.name if destination.region else "-"
    short = (destination.short_description or "").strip()
    if len(short) > 420:
        short = short[:419] + "..."

    lines = [f"<b>{name}</b>", f"Hudud: {region_name}"]
    if short:
        lines.append(short)
    if destination.address:
        lines.append(f"Manzil: {destination.address}")
    if destination.visiting_hours:
        lines.append(f"Ish vaqti: {destination.visiting_hours}")
    if destination.best_time_to_visit:
        lines.append(f"Eng yaxshi vaqt: {destination.best_time_to_visit}")
    if destination.contact_phone:
        lines.append(f"Aloqa: {destination.contact_phone}")
    if destination.google_maps_url:
        lines.append(destination.google_maps_url)
    return "\n".join(lines)[:1020]


def destination_image_input(destination: Destination):
    for field_name in ("cover_image", "hero_image"):
        image_field = getattr(destination, field_name, None)
        if not image_field:
            continue
        try:
            image_field.open("rb")
            content = image_field.read()
            if content:
                filename = os.path.basename(image_field.name) or "destination.jpg"
                return BufferedInputFile(content, filename=filename)
        except Exception:
            continue
        finally:
            try:
                image_field.close()
            except Exception:
                pass
    return None


def culture_image_input(item: CultureItem):
    image_field = getattr(item, "image", None)
    if not image_field:
        return None

    try:
        image_field.open("rb")
        content = image_field.read()
        if content:
            filename = os.path.basename(image_field.name) or "culture.jpg"
            return BufferedInputFile(content, filename=filename)
    except Exception:
        return None
    finally:
        try:
            image_field.close()
        except Exception:
            pass


@sync_to_async
def fetch_places(kind: str, limit: int = 6):
    qs = Destination.objects.filter(
        is_active=True,
        region__is_active=True,
    ).select_related("region").order_by("-is_featured", "-average_rating", "sort_order", "name")

    if kind == "pilgrimage":
        qs = qs.filter(destination_type__in=[Destination.DestinationType.PILGRIMAGE, Destination.DestinationType.MIXED])
    elif kind == "tourist":
        qs = qs.filter(destination_type__in=[Destination.DestinationType.TOURIST, Destination.DestinationType.MIXED])
    elif kind == "recreation":
        qs = qs.filter(
            Q(categories__slug__in=["nature", "resort", "recreation", "dam-olish"])
            | Q(name__icontains="bog")
            | Q(name__icontains="park")
            | Q(name__icontains="xonobod")
            | Q(short_description__icontains="dam olish")
        ).distinct()
    elif kind == "museums":
        qs = qs.filter(
            Q(categories__slug__in=["museum", "historical", "muzey"])
            | Q(name__icontains="muzey")
            | Q(name__icontains="museum")
            | Q(short_description__icontains="muzey")
        ).distinct()
    elif kind == "food":
        qs = qs.filter(
            Q(categories__slug__in=["food", "gastro", "restaurant", "ovqatlanish"])
            | Q(name__icontains="osh")
            | Q(name__icontains="palov")
            | Q(name__icontains="somsa")
            | Q(name__icontains="kabob")
            | Q(short_description__icontains="ovqat")
        ).distinct()

    return list(qs[:limit])


@sync_to_async
def fetch_random_place():
    ids = list(
        Destination.objects.filter(
            is_active=True,
            region__is_active=True,
        ).values_list("id", flat=True)
    )
    if not ids:
        return None
    random_id = random.choice(ids)
    return Destination.objects.select_related("region").filter(id=random_id).first()


@sync_to_async
def fetch_places_with_coords():
    return list(
        Destination.objects.filter(
            is_active=True,
            region__is_active=True,
            latitude__isnull=False,
            longitude__isnull=False,
        ).select_related("region")
    )


@sync_to_async
def fetch_culture_items(limit: int = 6):
    return list(
        CultureItem.objects.filter(is_active=True).order_by("-is_featured", "sort_order", "title")[:limit]
    )


async def send_destination(message: Message, destination: Destination, distance_km: float | None = None):
    caption = make_caption(destination)
    map_url = destination.google_maps_url or destination.yandex_maps_url or None
    if distance_km is not None:
        caption = f"{caption}\nMasofa: {distance_km:.1f} km"

    photo = destination_image_input(destination)
    if photo:
        await message.answer_photo(photo=photo, caption=caption, reply_markup=build_place_inline(map_url))
        return

    await message.answer(text=caption, reply_markup=build_place_inline(map_url), disable_web_page_preview=True)


async def send_culture_item(message: Message, item: CultureItem):
    short = (item.short_description or "").strip()
    if len(short) > 420:
        short = short[:419] + "..."
    caption = f"<b>{item.title}</b>"
    if short:
        caption += f"\n{short}"
    if item.detail_url:
        caption += f"\n{item.detail_url}"
    caption = caption[:1020]

    photo = culture_image_input(item)
    if photo:
        await message.answer_photo(photo=photo, caption=caption)
        return
    await message.answer(caption, disable_web_page_preview=True)


def register_handlers(dp: Dispatcher):
    @dp.message(CommandStart())
    async def start_handler(message: Message):
        await message.answer("Andijon tourism botga xush kelibsiz.", reply_markup=build_main_menu())

    @dp.message(TgCommand("help"))
    async def help_handler(message: Message):
        await message.answer(
            "/start - menyu\n/help - yordam\n/location - lokatsiya yuborish bo'limi\n"
            "Bo'limlar: Joylar, Ziyoratgohlar, Dam olish, Muzeylar, Ovqatlanish, Hunarmandchilik"
        )

    @dp.message(TgCommand("location"))
    async def location_handler(message: Message):
        await message.answer(LOCATION_PROMPT, reply_markup=build_location_menu())

    @dp.message(F.location)
    async def location_payload_handler(message: Message):
        places = await fetch_places_with_coords()
        if not places:
            await message.answer("Koordinata bilan joy topilmadi.")
            return

        user_lat = float(message.location.latitude)
        user_lon = float(message.location.longitude)
        ranked = []
        for place in places:
            dist = haversine_km(user_lat, user_lon, float(place.latitude), float(place.longitude))
            ranked.append((dist, place))
        ranked.sort(key=lambda row: row[0])

        await message.answer("Sizga eng yaqin joylar:")
        for dist, place in ranked[:5]:
            await send_destination(message, place, distance_km=dist)

    @dp.message(F.text == MENU_PLACES)
    async def places_handler(message: Message):
        places = await fetch_places(kind="tourist", limit=6)
        if not places:
            await message.answer("Joylar topilmadi.")
            return
        for place in places:
            await send_destination(message, place)

    @dp.message(F.text == MENU_PILGRIMAGE)
    async def pilgrimage_handler(message: Message):
        places = await fetch_places(kind="pilgrimage", limit=6)
        if not places:
            await message.answer("Ziyoratgohlar topilmadi.")
            return
        for place in places:
            await send_destination(message, place)

    @dp.message(F.text == MENU_RANDOM)
    async def random_handler(message: Message):
        place = await fetch_random_place()
        if not place:
            await message.answer("Hozircha joy topilmadi.")
            return
        await send_destination(message, place)

    @dp.message(F.text == MENU_RECREATION)
    async def recreation_handler(message: Message):
        places = await fetch_places(kind="recreation", limit=6)
        if not places:
            await message.answer("Dam olish maskanlari topilmadi.")
            return
        for place in places:
            await send_destination(message, place)

    @dp.message(F.text == MENU_MUSEUMS)
    async def museums_handler(message: Message):
        places = await fetch_places(kind="museums", limit=6)
        if not places:
            await message.answer("Muzeylar topilmadi.")
            return
        for place in places:
            await send_destination(message, place)

    @dp.message(F.text == MENU_FOOD)
    async def food_handler(message: Message):
        places = await fetch_places(kind="food", limit=6)
        if not places:
            await message.answer("Ovqatlanish joylari topilmadi.")
            return
        for place in places:
            await send_destination(message, place)

    @dp.message(F.text == MENU_CRAFTS)
    async def crafts_handler(message: Message):
        items = await fetch_culture_items(limit=8)
        if not items:
            await message.answer("Hunarmandchilik bo'limida ma'lumot topilmadi.")
            return
        for item in items:
            await send_culture_item(message, item)

    @dp.message(F.text == MENU_NEARBY)
    async def nearby_menu_handler(message: Message):
        await message.answer(LOCATION_PROMPT, reply_markup=build_location_menu())

    @dp.message(F.text == MENU_SEND_LOCATION)
    async def send_location_handler(message: Message):
        await message.answer(LOCATION_PROMPT, reply_markup=build_location_menu())

    @dp.message(F.text == MENU_BACK)
    async def back_menu_handler(message: Message):
        await message.answer("Asosiy menyu.", reply_markup=build_main_menu())


async def start_bot(token: str):
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    register_handlers(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


class Command(BaseCommand):
    help = "Tourism Telegram botini ishga tushiradi (rasmlar bilan)."

    def add_arguments(self, parser):
        parser.add_argument("--token", type=str, default="", help="Telegram bot token (ixtiyoriy).")

    def handle(self, *args, **options):
        if Bot is None or Dispatcher is None:
            raise CommandError("aiogram topilmadi. pip install -r requirements/base.txt")

        token = (options.get("token") or settings.TELEGRAM_BOT_TOKEN or "").strip()
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN topilmadi.")

        self.stdout.write(self.style.SUCCESS("Bot ishga tushmoqda (rasmlar bilan)..."))
        try:
            asyncio.run(start_bot(token))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Bot to'xtatildi."))
