# Uzbekistan Tourism API Docs

## Maqsad

Bu hujjat O'zbekistondagi turistik joylar va ziyoratgohlar haqida ma'lumot beradigan sayt uchun API contract hisoblanadi. Asosiy maqsad:

- bosh sahifa uchun tayyor blokli JSON berish,
- joylar ro'yxati sahifasini filter va pagination bilan ishlatish,
- joy detail sahifasida to'liq ma'lumot, galereya va yo'nalishlarni ko'rsatish,
- xarita sahifasiga yengil marker JSON berish,
- qidiruv va FAQ bloklarini alohida endpoint bilan ta'minlash.

## Umumiy qoidalar

- Base URL: `/api/v1`
- Barcha response lar `application/json`
- Field naming: `snake_case`
- Sana formati: `YYYY-MM-DD`
- Rasm URL lari to'liq URL bo'lishi kerak
- `entry_fee` qiymati son yoki `null`
- `average_rating` son ko'rinishida qaytadi: `4.7`
- List endpointlar pagination bilan ishlaydi

## Standart pagination formati

```json
{
  "count": 125,
  "next": "https://example.com/api/v1/places/?page=2",
  "previous": null,
  "results": []
}
```

## Sahifa va endpoint mapping

| Sahifa                              | Endpoint                                            | Maqsad                                                               |
| ----------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------- |
| Bosh sahifa                         | `GET /api/v1/home/`                               | Hero, tavsiya etilgan joylar, ziyoratgohlar, hududlar, kategoriyalar |
| Joylar ro'yxati                     | `GET /api/v1/places/`                             | Barcha joylar, filter, qidiruv, pagination                           |
| Ziyoratgohlar sahifasi              | `GET /api/v1/places/?destination_type=pilgrimage` | Faqat ziyoratgohlar ro'yxati                                         |
| Turistik joylar sahifasi            | `GET /api/v1/places/?destination_type=tourist`    | Faqat turistik joylar ro'yxati                                       |
| Viloyatlar sahifasi                 | `GET /api/v1/regions/`                            | Viloyatlar ro'yxati va har birida joylar soni                        |
| Viloyat ichki sahifasi              | `GET /api/v1/regions/{slug}/`                     | Bitta viloyat va unga tegishli joylar                                |
| Joy detail sahifasi                 | `GET /api/v1/places/{slug}/`                      | To'liq ma'lumot, galereya, yaqin joylar, sharhlar, FAQ               |
| Joy detail ichidagi yo'nalish bloki | `GET /api/v1/places/{slug}/routes/`               | Mashina, avtobus, poyezd va boshqa yo'nalishlar                      |
| Sayohat yo'nalishlari               | `GET /api/v1/routes/`                             | Yo'nalishlar ro'yxati (filter, pagination)                           |
| Sayohat yo'nalishi detail           | `GET /api/v1/routes/{id}/`                        | Bitta yo'nalish haqida to'liq ma'lumot                               |
| Xarita sahifasi                     | `GET /api/v1/map/places/`                         | Faqat marker uchun yengil JSON                                       |
| FAQ sahifasi                        | `GET /api/v1/faqs/`                               | Global yoki bitta joyga tegishli savol-javoblar                      |
| Search suggest                      | `GET /api/v1/search/suggestions/?q=`              | Header qidiruv uchun tezkor takliflar                                |
| Filter data                         | `GET /api/v1/meta/filters/`                       | Region, kategoriya va count lar                                      |

## Reusable object lar

### `region_item`

```json
{
  "id": "9d6bde53-b6df-4d3e-a26d-ecf974a2e001",
  "name": "Samarqand viloyati",
  "slug": "samarqand-viloyati"
}
```

### `category_item`

```json
{
  "id": "4de7d0c5-d2a4-43b7-8a57-e9e85ab71b11",
  "name": "Ziyoratgoh",
  "slug": "ziyoratgoh",
  "icon": "mosque"
}
```

### `amenity_item`

```json
{
  "id": "f61ec4ae-2f38-4b14-a6b9-6af2b5911308",
  "name": "Avtoturargoh",
  "slug": "avtoturargoh",
  "icon": "car"
}
```

### `place_card`

Bu format card, list, carousel va qidiruv natijalarida bir xil ishlatiladi.

```json
{
  "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
  "name": "Imom Buxoriy majmuasi",
  "slug": "imom-buxoriy-majmuasi",
  "destination_type": "pilgrimage",
  "destination_type_label": "Ziyoratgoh",
  "tagline": "Samarqanddagi mashhur ziyorat maskani",
  "short_description": "Tarixiy va muqaddas maskan.",
  "district": "Payariq tumani",
  "region": {
    "id": "9d6bde53-b6df-4d3e-a26d-ecf974a2e001",
    "name": "Samarqand viloyati",
    "slug": "samarqand-viloyati"
  },
  "categories": [
    {
      "id": "4de7d0c5-d2a4-43b7-8a57-e9e85ab71b11",
      "name": "Ziyoratgoh",
      "slug": "ziyoratgoh",
      "icon": "mosque"
    }
  ],
  "cover_image": "https://example.com/media/destinations/covers/imom-buxoriy.jpg",
  "hero_image": "https://example.com/media/destinations/heroes/imom-buxoriy.jpg",
  "average_rating": 4.8,
  "review_count": 128,
  "best_time_to_visit": "Mart - May, Sentyabr - Noyabr",
  "entry_fee": null,
  "google_maps_url": "https://maps.google.com/...",
  "yandex_maps_url": "https://yandex.uz/maps/..."
}
```

### `route_item`

```json
{
  "id": "8d14b5f7-eaf2-4659-9f17-70bf844011b3",
  "title": "Toshkentdan mashinada",
  "transport_type": "car",
  "transport_type_label": "Mashina",
  "starting_point": "Toshkent shahri",
  "route_description": "M39 yo'li orqali Samarqandga, keyin Payariq tomonga harakat qilinadi.",
  "distance_km": 295.5,
  "duration_text": "4 soat 20 daqiqa",
  "map_url": "https://maps.google.com/...",
  "notes": "Yo'lda 2 ta pullik uchastka bo'lishi mumkin."
}
```

### `review_item`

```json
{
  "id": "db68f870-bd88-4d12-91c3-e6fe15b61511",
  "author_name": "Aziza",
  "rating": 5,
  "title": "Juda fayzli joy",
  "body": "Oilaviy tashrif uchun yaxshi joy ekan.",
  "visited_at": "2026-02-12"
}
```

### `faq_item`

```json
{
  "id": "7d8d2964-4c48-49d1-b6bf-e2051b014913",
  "question": "Bu joyga kirish pullikmi?",
  "answer": "Hozircha kirish bepul, ammo ayrim xizmatlar pullik bo'lishi mumkin."
}
```

## 1. Bosh sahifa

### Endpoint

`GET /api/v1/home/`

### Optional query param lar

- `lat=41.3111`
- `lng=69.2797`

`lat` va `lng` yuborilsa, `nearby_tourist_objects` foydalanuvchiga yaqin joylar bilan to'ldiriladi. Agar koordinata kelmasa, backend default ravishda mashhur yaqin joylarni qaytaradi.

### Response

```json
{
  "banner": {
    "title": "O'zbekistondagi eng mashhur turistik joylar va ziyoratgohlar",
    "subtitle": "Hududlar bo'yicha izlang, joy haqida o'qing va yo'nalishni toping.",
    "featured_image": "https://example.com/media/banners/home-hero.jpg",
    "cta_primary": {
      "label": "Joylarni ko'rish",
      "url": "/places/"
    },
    "cta_secondary": {
      "label": "Xaritada ko'rish",
      "url": "/map/"
    }
  },
  "about_uzbekistan": {
    "title": "O'zbekiston haqida",
    "description": "O'zbekiston qadimiy shaharlar, ziyoratgohlar, tabiiy maskanlar va boy madaniy merosga ega mamlakat.",
    "image": "https://example.com/media/banners/about-uzbekistan.jpg",
    "highlights": [
      "14 ta hudud",
      "Yuzlab tarixiy obyektlar",
      "Ichki turizm va ziyorat uchun qulay yo'nalishlar"
    ]
  },
  "stats": {
    "regions_count": 14,
    "places_count": 320,
    "pilgrimage_count": 95,
    "tourist_count": 225
  },
  "popular_tourist_places": [
    {
      "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl.",
      "district": "Samarqand shahri",
      "region": {
        "id": "9d6bde53-b6df-4d3e-a26d-ecf974a2e001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [],
      "cover_image": "https://example.com/media/destinations/covers/registon.jpg",
      "hero_image": "https://example.com/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/...",
      "yandex_maps_url": "https://yandex.uz/maps/..."
    }
  ],
  "pilgrimage_places": [],
  "recommended_routes": [
    {
      "id": "route-001",
      "title": "Samarqand - Buxoro tarixiy yo'nalishi",
      "summary": "2-3 kunlik mashhur tarixiy sayohat marshruti.",
      "days": 3,
      "transport_type": "car",
      "transport_type_label": "Mashina",
      "distance_km": 280,
      "duration_text": "3 kun / 2 tun",
      "start_region": "Samarqand viloyati",
      "end_region": "Buxoro viloyati",
      "map_url": "https://maps.google.com/...",
      "places": [
        {
          "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
          "name": "Registon maydoni",
          "slug": "registon-maydoni",
          "cover_image": "https://example.com/media/destinations/covers/registon.jpg"
        },
        {
          "id": "1fd41048-a204-4d2a-9717-d74643b0ab3b",
          "name": "Poi Kalon majmuasi",
          "slug": "poi-kalon-majmuasi",
          "cover_image": "https://example.com/media/destinations/covers/poi-kalon.jpg"
        }
      ]
    }
  ],
  "nearby_tourist_objects": [
    {
      "id": "2fd41048-a204-4d2a-9717-d74643b0ab4c",
      "name": "Amir Temur xiyoboni",
      "slug": "amir-temur-xiyoboni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Toshkent markazidagi mashhur maskan",
      "short_description": "Yurish va sayr qilish uchun qulay markaziy hudud.",
      "district": "Toshkent shahri",
      "region": {
        "id": "3d6bde53-b6df-4d3e-a26d-ecf974a2e005",
        "name": "Toshkent shahri",
        "slug": "toshkent-shahri"
      },
      "categories": [],
      "cover_image": "https://example.com/media/destinations/covers/amir-temur.jpg",
      "hero_image": "https://example.com/media/destinations/heroes/amir-temur.jpg",
      "average_rating": 4.7,
      "review_count": 89,
      "best_time_to_visit": "Yil davomida",
      "entry_fee": null,
      "google_maps_url": "https://maps.google.com/...",
      "yandex_maps_url": "https://yandex.uz/maps/..."
    }
  ],
  "regions": [],
  "categories": []
}
```

### Frontend ishlatishi

- Banner: `banner`
- O'zbekiston haqida blok: `about_uzbekistan`
- Home stats: `stats`
- Mashhur turistik joylar: `popular_tourist_places`
- Ziyoratgohlar carousel: `pilgrimage_places`
- Tavsiya etilgan sayohat yo'nalishlari: `recommended_routes`
- Yaqindagi turistik obyektlar: `nearby_tourist_objects`
- Hudud bo'yicha blok: `regions`
- Kategoriya filter badge lar: `categories`

## 2. Joylar ro'yxati sahifasi

### Endpoint

`GET /api/v1/places/`

### Query param lar

- `page=1`
- `page_size=12`
- `q=registon`
- `region=samarqand-viloyati`
- `category=ziyoratgoh`
- `destination_type=tourist|pilgrimage|mixed`
- `is_featured=true`
- `ordering=name|-created_at|-average_rating`

### Response

```json
{
  "count": 320,
  "next": "https://example.com/api/v1/places/?page=2",
  "previous": null,
  "results": [
    {
      "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl.",
      "district": "Samarqand shahri",
      "region": {
        "id": "9d6bde53-b6df-4d3e-a26d-ecf974a2e001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [],
      "cover_image": "https://example.com/media/destinations/covers/registon.jpg",
      "hero_image": "https://example.com/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/...",
      "yandex_maps_url": "https://yandex.uz/maps/..."
    }
  ]
}
```

### Frontend ishlatishi

- Listing cards: `results`
- Pagination: `count`, `next`, `previous`
- Filter state query param orqali boshqariladi

## 3. Joy detail sahifasi

### Endpoint

`GET /api/v1/places/{slug}/`

### Response

```json
{
  "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
  "name": "Imom Buxoriy majmuasi",
  "slug": "imom-buxoriy-majmuasi",
  "destination_type": "pilgrimage",
  "destination_type_label": "Ziyoratgoh",
  "tagline": "Samarqanddagi muqaddas maskan",
  "short_description": "Tarixiy va muqaddas maskan.",
  "overview": "Bu joy haqida batafsil matn.",
  "history": "Tarixiy ma'lumotlar shu yerda bo'ladi.",
  "how_to_get_there": "Samarqand shahridan avtomobil yoki avtobus orqali boriladi.",
  "visiting_hours": "08:00 - 20:00",
  "address": "Samarqand viloyati, Payariq tumani",
  "district": "Payariq tumani",
  "landmark": "Asosiy katta masjid yaqinida",
  "latitude": 39.654321,
  "longitude": 66.975421,
  "best_time_to_visit": "Mart - May",
  "recommended_visit_duration": "1-2 soat",
  "entry_fee": null,
  "ticket_notes": "Kirish bepul",
  "contact_phone": "+998901234567",
  "official_website": "https://example.uz",
  "google_maps_url": "https://maps.google.com/...",
  "yandex_maps_url": "https://yandex.uz/maps/...",
  "hero_image": "https://example.com/media/destinations/heroes/imom-buxoriy.jpg",
  "cover_image": "https://example.com/media/destinations/covers/imom-buxoriy.jpg",
  "average_rating": 4.8,
  "review_count": 128,
  "region": {
    "id": "9d6bde53-b6df-4d3e-a26d-ecf974a2e001",
    "name": "Samarqand viloyati",
    "slug": "samarqand-viloyati"
  },
  "categories": [
    {
      "id": "4de7d0c5-d2a4-43b7-8a57-e9e85ab71b11",
      "name": "Ziyoratgoh",
      "slug": "ziyoratgoh",
      "icon": "mosque"
    }
  ],
  "amenities": [
    {
      "id": "f61ec4ae-2f38-4b14-a6b9-6af2b5911308",
      "name": "Avtoturargoh",
      "slug": "avtoturargoh",
      "icon": "car"
    }
  ],
  "gallery": [
    {
      "id": "de312fab-5b4a-4713-a99c-4c580343a0b7",
      "image": "https://example.com/media/destinations/gallery/imom-buxoriy-1.jpg",
      "alt_text": "Majmua tashqi ko'rinishi",
      "caption": "Asosiy kirish qismi",
      "is_cover": true,
      "sort_order": 0
    }
  ],
  "nearby_places": [
    {
      "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl.",
      "district": "Samarqand shahri",
      "region": {
        "id": "9d6bde53-b6df-4d3e-a26d-ecf974a2e001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [],
      "cover_image": "https://example.com/media/destinations/covers/registon.jpg",
      "hero_image": "https://example.com/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/...",
      "yandex_maps_url": "https://yandex.uz/maps/..."
    }
  ],
  "routes": [],
  "reviews_preview": [],
  "faqs_preview": []
}
```

### Frontend ishlatishi

- Hero image va title: yuqori section
- `overview`, `history`, `how_to_get_there`: content section
- `gallery`: image gallery
- `amenities`: qulaylik badge lari
- `nearby_places`: related places
- `routes`: joyga qanday borish bloki
- `reviews_preview`: detail page sharh preview
- `faqs_preview`: detail page FAQ preview

## 4. Joy detail ichidagi yo'nalish bloki

### Endpoint

`GET /api/v1/places/{slug}/routes/`

### Response

```json
{
  "destination": {
    "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
    "name": "Imom Buxoriy majmuasi",
    "slug": "imom-buxoriy-majmuasi"
  },
  "results": [
    {
      "id": "8d14b5f7-eaf2-4659-9f17-70bf844011b3",
      "title": "Toshkentdan mashinada",
      "transport_type": "car",
      "transport_type_label": "Mashina",
      "starting_point": "Toshkent shahri",
      "route_description": "M39 yo'li orqali Samarqandga harakat qilinadi.",
      "distance_km": 295.5,
      "duration_text": "4 soat 20 daqiqa",
      "map_url": "https://maps.google.com/...",
      "notes": "Yo'l holatini oldindan tekshirish tavsiya etiladi."
    }
  ]
}
```

## 5. Xarita sahifasi

### Endpoint

`GET /api/v1/map/places/`

### Query param lar

- `region=samarqand-viloyati`
- `category=ziyoratgoh`
- `destination_type=pilgrimage`

### Response

Xarita uchun yengil format. Bu yerda detail dagi barcha field lar qaytmasligi kerak.

```json
{
  "results": [
    {
      "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "latitude": 39.654321,
      "longitude": 66.975421,
      "region_name": "Samarqand viloyati",
      "cover_image": "https://example.com/media/destinations/covers/imom-buxoriy.jpg",
      "google_maps_url": "https://maps.google.com/..."
    }
  ]
}
```

## 6. FAQ sahifasi

### Endpoint

`GET /api/v1/faqs/`

### Query param lar

- `destination_slug=imom-buxoriy-majmuasi`

### Response

```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "7d8d2964-4c48-49d1-b6bf-e2051b014913",
      "question": "Bu joyga kirish pullikmi?",
      "answer": "Hozircha kirish bepul.",
      "destination": {
        "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
        "name": "Imom Buxoriy majmuasi",
        "slug": "imom-buxoriy-majmuasi"
      }
    }
  ]
}
```

## 7. Search suggest

### Endpoint

`GET /api/v1/search/suggestions/?q=imom`

### Response

```json
{
  "query": "imom",
  "results": [
    {
      "type": "destination",
      "id": "0fd41048-a204-4d2a-9717-d74643b0ab2a",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "region_name": "Samarqand viloyati",
      "cover_image": "https://example.com/media/destinations/covers/imom-buxoriy.jpg"
    }
  ]
}
```

## 8. Filter metadata

### Endpoint

`GET /api/v1/meta/filters/`

### Response

```json
{
  "destination_types": [
    {
      "value": "tourist",
      "label": "Turistik joy",
      "count": 225
    },
    {
      "value": "pilgrimage",
      "label": "Ziyoratgoh",
      "count": 95
    }
  ],
  "regions": [
    {
      "id": "9d6bde53-b6df-4d3e-a26d-ecf974a2e001",
      "name": "Samarqand viloyati",
      "slug": "samarqand-viloyati",
      "count": 42
    }
  ],
  "categories": [
    {
      "id": "4de7d0c5-d2a4-43b7-8a57-e9e85ab71b11",
      "name": "Ziyoratgoh",
      "slug": "ziyoratgoh",
      "icon": "mosque",
      "count": 95
    }
  ]
}
```

## Tavsiya etilgan serializer struktura

- `RegionListSerializer`
- `CategoryListSerializer`
- `AmenitySerializer`
- `DestinationCardSerializer`
- `DestinationDetailSerializer`
- `DestinationImageSerializer`
- `RouteGuideSerializer`
- `ReviewSerializer`
- `FAQSerializer`
- `HomePageSerializer`

## Tavsiya etilgan view lar

- `HomeAPIView`
- `DestinationListAPIView`
- `RegionListAPIView`
- `RegionDetailAPIView`
- `DestinationDetailAPIView`
- `DestinationRoutesAPIView`
- `RouteGuideListAPIView`
- `RouteGuideDetailAPIView`
- `MapDestinationAPIView`
- `FAQListAPIView`
- `SearchSuggestionAPIView`
- `FilterMetaAPIView`

## Eslatma

Agar frontend detail sahifada hamma narsani bitta request bilan ochsa, `GET /api/v1/places/{slug}/` ichida `routes`, `reviews_preview`, `faqs_preview` qaytarilishi kerak. Agar page lazy-load ishlatsa, bu bloklarni alohida endpoint bilan olish yaxshiroq.
