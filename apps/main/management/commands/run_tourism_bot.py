import asyncio
import math
import random
from collections import defaultdict

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.html import escape

from apps.main.models import CultureItem, Destination, RouteGuide

try:
    from aiogram import Bot, Dispatcher, F
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.filters import Command, CommandStart
    from aiogram.types import CallbackQuery, KeyboardButton, Message
    from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
except ImportError:  # pragma: no cover - dependency guard
    Bot = None
    Dispatcher = None


SUPPORTED_LANGS = ("uz", "ru", "en")
DEFAULT_RESULTS_LIMIT = 5


TEXTS = {
    "welcome": {
        "uz": "Assalomu alaykum. Andijon tourism botiga xush kelibsiz.\nKerakli bolimni tanlang.",
        "ru": "Welcome. Choose a section from the menu.",
        "en": "Welcome. Choose a section from the menu.",
    },
    "help": {
        "uz": "Asosiy buyruqlar:\n/start - menyuni ochish\n/lang - til tanlash\n/location - yaqin joylarni topish",
        "ru": "Main commands:\n/start\n/lang\n/location",
        "en": "Main commands:\n/start\n/lang\n/location",
    },
    "choose_lang": {
        "uz": "Tilni tanlang:",
        "ru": "Choose language:",
        "en": "Choose language:",
    },
    "lang_saved": {
        "uz": "Til saqlandi.",
        "ru": "Language updated.",
        "en": "Language updated.",
    },
    "no_data": {
        "uz": "Hozircha bu bolim uchun malumot topilmadi.",
        "ru": "No data found for this section.",
        "en": "No data found for this section.",
    },
    "send_location": {
        "uz": "Lokatsiyani yuboring, men sizga eng yaqin joylarni chiqaraman.",
        "ru": "Send your location to get nearby places.",
        "en": "Send your location to get nearby places.",
    },
    "nearby_title": {
        "uz": "Sizga eng yaqin joylar:",
        "ru": "Nearest places:",
        "en": "Nearest places:",
    },
    "unknown": {
        "uz": "Buyruq aniqlanmadi. /start ni bosing.",
        "ru": "Unknown command. Use /start.",
        "en": "Unknown command. Use /start.",
    },
    "map": {
        "uz": "Xaritada korish",
        "ru": "Open map",
        "en": "Open map",
    },
    "random": {
        "uz": "Tasodifiy joy",
        "ru": "Random place",
        "en": "Random place",
    },
    "routes_title": {
        "uz": "Tayyor marshrutlar:",
        "ru": "Suggested routes:",
        "en": "Suggested routes:",
    },
    "culture_title": {
        "uz": "Hunarmandchilik va madaniyat bo limi:",
        "ru": "Culture and crafts:",
        "en": "Culture and crafts:",
    },
    "ask_location_cmd": {
        "uz": "Yaqin joylarni topish uchun lokatsiya yuboring.",
        "ru": "Send your location.",
        "en": "Send your location.",
    },
    "no_coordinates": {
        "uz": "Koordinatasi bor joylar topilmadi.",
        "ru": "No places with coordinates.",
        "en": "No places with coordinates.",
    },
}


MENU_LABELS = {
    "pilgrimage": {"uz": "Ziyoratgohlar", "ru": "Pilgrimage", "en": "Pilgrimage"},
    "rest": {"uz": "Dam olish maskanlari", "ru": "Recreation", "en": "Recreation"},
    "museums": {"uz": "Muzeylar", "ru": "Museums", "en": "Museums"},
    "gastro": {"uz": "Ovqatlanish", "ru": "Gastro tourism", "en": "Gastro tourism"},
    "crafts": {"uz": "Hunarmandchilik", "ru": "Crafts", "en": "Crafts"},
    "routes": {"uz": "Interaktiv turlar", "ru": "Routes", "en": "Routes"},
    "nearby": {"uz": "Atrofimdagi joylar", "ru": "Nearby places", "en": "Nearby places"},
    "random": {"uz": "Random joy", "ru": "Random place", "en": "Random place"},
    "change_lang": {"uz": "Tilni almashtirish", "ru": "Change language", "en": "Change language"},
    "back_menu": {"uz": "Menyuga qaytish", "ru": "Back to menu", "en": "Back to menu"},
    "send_location": {"uz": "Lokatsiyani yuborish", "ru": "Send location", "en": "Send location"},
}


LANG_TITLES = {"uz": "UZ", "ru": "RU", "en": "EN"}


def t(lang: str, key: str) -> str:
    values = TEXTS.get(key, {})
    return values.get(lang) or values.get("uz", "")


def menu_label(action: str, lang: str) -> str:
    values = MENU_LABELS.get(action, {})
    return values.get(lang) or values.get("uz", action)


def translated_attr(instance, field_name: str, lang: str) -> str:
    localized = getattr(instance, f"{field_name}_{lang}", None)
    if localized:
        return str(localized)
    return str(getattr(instance, field_name, "") or "")


def truncate(text: str, limit: int = 280) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1]}..."


def map_url_for_destination(destination: Destination) -> str:
    if destination.google_maps_url:
        return destination.google_maps_url
    if destination.yandex_maps_url:
        return destination.yandex_maps_url
    if destination.latitude is not None and destination.longitude is not None:
        return f"https://maps.google.com/?q={destination.latitude},{destination.longitude}"
    return ""


def format_destination_message(destination: Destination, lang: str) -> str:
    name = escape(translated_attr(destination, "name", lang))
    region = escape(translated_attr(destination.region, "name", lang))
    summary = escape(truncate(translated_attr(destination, "short_description", lang), 240))
    map_url = map_url_for_destination(destination)

    lines = [f"<b>{name}</b>", f"Region: {region}"]
    if summary:
        lines.append(summary)
    if map_url:
        lines.append(f"<a href=\"{escape(map_url)}\">{escape(t(lang, 'map'))}</a>")
    return "\n".join(lines)


def format_route_message(route: RouteGuide, lang: str) -> str:
    title = escape(translated_attr(route, "title", lang))
    description = escape(truncate(translated_attr(route, "route_description", lang), 220))
    start = escape(translated_attr(route, "starting_point", lang))
    distance = route.distance_km if route.distance_km is not None else "-"
    duration = escape(translated_attr(route, "duration_text", lang))

    lines = [f"<b>{title}</b>", f"Start: {start}", f"Distance: {distance} km"]
    if duration:
        lines.append(f"Duration: {duration}")
    if description:
        lines.append(description)
    return "\n".join(lines)


def format_culture_message(item: CultureItem, lang: str) -> str:
    title = escape(translated_attr(item, "title", lang))
    summary = escape(truncate(translated_attr(item, "short_description", lang), 220))
    detail = escape(item.detail_url or "")
    lines = [f"<b>{title}</b>"]
    if summary:
        lines.append(summary)
    if detail:
        lines.append(detail)
    return "\n".join(lines)


def build_main_keyboard(lang: str):
    builder = ReplyKeyboardBuilder()
    for key in (
        "pilgrimage",
        "rest",
        "museums",
        "gastro",
        "crafts",
        "routes",
        "nearby",
        "random",
        "change_lang",
    ):
        builder.button(text=menu_label(key, lang))
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def build_location_keyboard(lang: str):
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=menu_label("send_location", lang), request_location=True))
    builder.row(KeyboardButton(text=menu_label("back_menu", lang)))
    return builder.as_markup(resize_keyboard=True)


def build_language_keyboard():
    builder = InlineKeyboardBuilder()
    for code in SUPPORTED_LANGS:
        builder.button(text=LANG_TITLES[code], callback_data=f"set_lang:{code}")
    builder.adjust(3)
    return builder.as_markup()


def build_destination_inline(destination: Destination, lang: str):
    builder = InlineKeyboardBuilder()
    map_url = map_url_for_destination(destination)
    if map_url:
        builder.button(text=t(lang, "map"), url=map_url)
    builder.button(text=t(lang, "random"), callback_data="action:random")
    builder.adjust(2)
    return builder.as_markup()


def resolve_action(text: str) -> str | None:
    incoming = (text or "").strip()
    if not incoming:
        return None
    for action, labels in MENU_LABELS.items():
        if incoming in labels.values():
            return action
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


@sync_to_async
def get_destinations_by_section(section: str, limit: int = DEFAULT_RESULTS_LIMIT):
    queryset = Destination.objects.filter(is_active=True, region__is_active=True).select_related("region").distinct()

    if section == "pilgrimage":
        queryset = queryset.filter(destination_type__in=[Destination.DestinationType.PILGRIMAGE, Destination.DestinationType.MIXED])
    elif section == "rest":
        queryset = queryset.filter(
            Q(categories__slug__in=["nature", "resort", "city"])
            | Q(name__icontains="xonobod")
            | Q(name__icontains="bog")
            | Q(short_description__icontains="dam olish")
        )
    elif section == "museums":
        queryset = queryset.filter(
            Q(categories__slug__in=["historical", "museum"])
            | Q(name__icontains="muzey")
            | Q(name__icontains="museum")
            | Q(short_description__icontains="muzey")
        )
    elif section == "gastro":
        queryset = queryset.filter(
            Q(categories__slug__in=["food", "gastro", "city"])
            | Q(name__icontains="osh")
            | Q(name__icontains="palov")
            | Q(name__icontains="somsa")
            | Q(name__icontains="kabob")
            | Q(short_description__icontains="ovqat")
        )
    elif section == "random":
        items = list(queryset.values_list("id", flat=True))
        if not items:
            return []
        selected_id = random.choice(items)
        selected = queryset.filter(id=selected_id).first()
        return [selected] if selected else []

    return list(queryset.order_by("-is_featured", "sort_order", "name")[:limit])


@sync_to_async
def get_culture_items(limit: int = DEFAULT_RESULTS_LIMIT):
    return list(CultureItem.objects.filter(is_active=True).order_by("-is_featured", "sort_order", "title")[:limit])


@sync_to_async
def get_routes(limit: int = DEFAULT_RESULTS_LIMIT):
    return list(
        RouteGuide.objects.filter(is_active=True, destination__is_active=True)
        .select_related("destination")
        .order_by("-is_featured", "sort_order", "title")[:limit]
    )


@sync_to_async
def get_destinations_with_coordinates():
    return list(
        Destination.objects.filter(
            is_active=True,
            region__is_active=True,
            latitude__isnull=False,
            longitude__isnull=False,
        ).select_related("region")
    )


async def send_destinations(message: Message, lang: str, section: str):
    destinations = await get_destinations_by_section(section=section)
    if not destinations:
        await message.answer(t(lang, "no_data"))
        return

    for destination in destinations:
        await message.answer(
            format_destination_message(destination, lang),
            disable_web_page_preview=True,
            reply_markup=build_destination_inline(destination, lang),
        )


async def send_culture_items(message: Message, lang: str):
    items = await get_culture_items()
    if not items:
        await message.answer(t(lang, "no_data"))
        return

    await message.answer(t(lang, "culture_title"))
    for item in items:
        await message.answer(format_culture_message(item, lang), disable_web_page_preview=True)


async def send_routes(message: Message, lang: str):
    routes = await get_routes()
    if not routes:
        await message.answer(t(lang, "no_data"))
        return

    await message.answer(t(lang, "routes_title"))
    for route in routes:
        await message.answer(format_route_message(route, lang), disable_web_page_preview=True)


async def send_nearby_places(message: Message, lang: str):
    if not message.location:
        await message.answer(t(lang, "send_location"), reply_markup=build_location_keyboard(lang))
        return

    places = await get_destinations_with_coordinates()
    if not places:
        await message.answer(t(lang, "no_coordinates"))
        return

    current_lat = float(message.location.latitude)
    current_lon = float(message.location.longitude)
    nearest = []
    for place in places:
        dist = haversine_km(current_lat, current_lon, float(place.latitude), float(place.longitude))
        nearest.append((dist, place))

    nearest.sort(key=lambda row: row[0])
    top = nearest[:DEFAULT_RESULTS_LIMIT]

    await message.answer(t(lang, "nearby_title"))
    for distance, place in top:
        payload = f"{format_destination_message(place, lang)}\nDistance: {distance:.1f} km"
        await message.answer(payload, disable_web_page_preview=True, reply_markup=build_destination_inline(place, lang))


def register_handlers(dispatcher: Dispatcher, user_languages: defaultdict):
    @dispatcher.message(CommandStart())
    async def start_handler(message: Message):
        user_id = message.from_user.id if message.from_user else 0
        lang = user_languages[user_id]
        await message.answer(t(lang, "welcome"), reply_markup=build_main_keyboard(lang))

    @dispatcher.message(Command("help"))
    async def help_handler(message: Message):
        user_id = message.from_user.id if message.from_user else 0
        lang = user_languages[user_id]
        await message.answer(t(lang, "help"))

    @dispatcher.message(Command("lang"))
    async def lang_handler(message: Message):
        user_id = message.from_user.id if message.from_user else 0
        lang = user_languages[user_id]
        await message.answer(t(lang, "choose_lang"), reply_markup=build_language_keyboard())

    @dispatcher.message(Command("location"))
    async def location_handler(message: Message):
        user_id = message.from_user.id if message.from_user else 0
        lang = user_languages[user_id]
        await message.answer(t(lang, "ask_location_cmd"), reply_markup=build_location_keyboard(lang))

    @dispatcher.callback_query(F.data.startswith("set_lang:"))
    async def callback_set_lang(callback: CallbackQuery):
        user_id = callback.from_user.id
        lang_code = callback.data.split(":", maxsplit=1)[-1]
        if lang_code not in SUPPORTED_LANGS:
            lang_code = "uz"
        user_languages[user_id] = lang_code

        await callback.message.answer(t(lang_code, "lang_saved"), reply_markup=build_main_keyboard(lang_code))
        await callback.answer()

    @dispatcher.callback_query(F.data == "action:random")
    async def callback_random(callback: CallbackQuery):
        user_id = callback.from_user.id
        lang = user_languages[user_id]
        await send_destinations(callback.message, lang, "random")
        await callback.answer()

    @dispatcher.message(F.location)
    async def location_payload_handler(message: Message):
        user_id = message.from_user.id if message.from_user else 0
        lang = user_languages[user_id]
        await send_nearby_places(message, lang)

    @dispatcher.message(F.text)
    async def menu_router(message: Message):
        user_id = message.from_user.id if message.from_user else 0
        lang = user_languages[user_id]
        action = resolve_action(message.text)

        if action == "pilgrimage":
            await send_destinations(message, lang, "pilgrimage")
            return
        if action == "rest":
            await send_destinations(message, lang, "rest")
            return
        if action == "museums":
            await send_destinations(message, lang, "museums")
            return
        if action == "gastro":
            await send_destinations(message, lang, "gastro")
            return
        if action == "crafts":
            await send_culture_items(message, lang)
            return
        if action == "routes":
            await send_routes(message, lang)
            return
        if action == "random":
            await send_destinations(message, lang, "random")
            return
        if action == "nearby":
            await message.answer(t(lang, "send_location"), reply_markup=build_location_keyboard(lang))
            return
        if action == "send_location":
            await message.answer(t(lang, "send_location"), reply_markup=build_location_keyboard(lang))
            return
        if action == "change_lang":
            await message.answer(t(lang, "choose_lang"), reply_markup=build_language_keyboard())
            return
        if action == "back_menu":
            await message.answer(t(lang, "welcome"), reply_markup=build_main_keyboard(lang))
            return

        await message.answer(t(lang, "unknown"), reply_markup=build_main_keyboard(lang))


async def run_bot(token: str):
    default_lang = (settings.TELEGRAM_BOT_DEFAULT_LANG or "uz").lower()
    if default_lang not in SUPPORTED_LANGS:
        default_lang = "uz"

    user_languages = defaultdict(lambda: default_lang)
    dispatcher = Dispatcher()
    register_handlers(dispatcher, user_languages)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


class Command(BaseCommand):
    help = "Mavjud tourism modellari asosida Telegram botni ishga tushiradi."

    def add_arguments(self, parser):
        parser.add_argument("--token", type=str, default="", help="Telegram bot token (ixtiyoriy).")

    def handle(self, *args, **options):
        if Bot is None or Dispatcher is None:
            raise CommandError("aiogram topilmadi. Avval: pip install -r requirements/base.txt")

        token = (options.get("token") or settings.TELEGRAM_BOT_TOKEN or "").strip()
        if not token:
            raise CommandError("Bot token topilmadi. .env ga TELEGRAM_BOT_TOKEN yozing yoki --token bering.")

        self.stdout.write(self.style.SUCCESS("Tourism bot ishga tushmoqda... Ctrl+C bilan to'xtatish mumkin."))
        try:
            asyncio.run(run_bot(token))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Bot to'xtatildi."))
