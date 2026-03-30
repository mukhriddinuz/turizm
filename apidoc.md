# Uzbekistan Tourism API Examples

Bu hujjatda frontend sahifalari uchun ishlatiladigan endpointlarning tayyor misollari berilgan. `API_DOCS.md` contract vazifasini bajaradi, bu fayl esa real response ko'rinishini ko'rsatadi.

- Base URL: `https://api.example.uz/api/v1`
- Content-Type: `application/json`
- Barcha misollar `200 OK` holati uchun yozilgan

## 1. Bosh sahifa

### Request

```http
GET /api/v1/home/?lat=41.3111&lng=69.2797 HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "banner": {
    "title": "O'zbekistondagi eng mashhur turistik joylar va ziyoratgohlar",
    "subtitle": "Hududlar bo'yicha izlang, joylar haqida o'qing va yo'nalishni toping.",
    "featured_image": "https://api.example.uz/media/banners/home-hero.jpg",
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
    "image": "https://api.example.uz/media/banners/about-uzbekistan.jpg",
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
      "id": "11000000-0000-0000-0000-000000000001",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl va Samarqandning eng mashhur ramzlaridan biri.",
      "district": "Samarqand shahri",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000001",
          "name": "Tarixiy obida",
          "slug": "tarixiy-obida",
          "icon": "landmark"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/registon.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/?q=registon",
      "yandex_maps_url": "https://yandex.uz/maps/?text=registon"
    },
    {
      "id": "11000000-0000-0000-0000-000000000002",
      "name": "Xiva Ichan-Qal'a",
      "slug": "xiva-ichan-qala",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Ochiq osmon ostidagi muzey shahar",
      "short_description": "UNESCO merosi ro'yxatiga kirgan qadimiy tarixiy hudud.",
      "district": "Xiva shahri",
      "region": {
        "id": "21000000-0000-0000-0000-000000000002",
        "name": "Xorazm viloyati",
        "slug": "xorazm-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000001",
          "name": "Tarixiy obida",
          "slug": "tarixiy-obida",
          "icon": "landmark"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/ichanqala.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/ichanqala.jpg",
      "average_rating": 4.8,
      "review_count": 295,
      "best_time_to_visit": "Aprel - Oktyabr",
      "entry_fee": 75000.0,
      "google_maps_url": "https://maps.google.com/?q=ichan+qala",
      "yandex_maps_url": "https://yandex.uz/maps/?text=ichan%20qala"
    }
  ],
  "pilgrimage_places": [
    {
      "id": "11000000-0000-0000-0000-000000000003",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "tagline": "Samarqanddagi muqaddas ziyorat maskani",
      "short_description": "Islom olamidagi muhim ziyorat joylaridan biri.",
      "district": "Payariq tumani",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000002",
          "name": "Ziyoratgoh",
          "slug": "ziyoratgoh",
          "icon": "mosque"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/imom-buxoriy.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/imom-buxoriy.jpg",
      "average_rating": 4.8,
      "review_count": 128,
      "best_time_to_visit": "Mart - May, Sentyabr - Noyabr",
      "entry_fee": null,
      "google_maps_url": "https://maps.google.com/?q=imam+bukhari+complex",
      "yandex_maps_url": "https://yandex.uz/maps/?text=imom%20buxoriy"
    }
  ],
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
      "map_url": "https://maps.google.com/?q=samarkand+bukhara+route",
      "places": [
        {
          "id": "11000000-0000-0000-0000-000000000001",
          "name": "Registon maydoni",
          "slug": "registon-maydoni",
          "cover_image": "https://api.example.uz/media/destinations/covers/registon.jpg"
        },
        {
          "id": "11000000-0000-0000-0000-000000000006",
          "name": "Poi Kalon majmuasi",
          "slug": "poi-kalon-majmuasi",
          "cover_image": "https://api.example.uz/media/destinations/covers/poi-kalon.jpg"
        }
      ]
    }
  ],
  "nearby_tourist_objects": [
    {
      "id": "11000000-0000-0000-0000-000000000007",
      "name": "Amir Temur xiyoboni",
      "slug": "amir-temur-xiyoboni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Toshkent markazidagi mashhur maskan",
      "short_description": "Yurish va sayr qilish uchun qulay markaziy hudud.",
      "district": "Toshkent shahri",
      "region": {
        "id": "21000000-0000-0000-0000-000000000004",
        "name": "Toshkent shahri",
        "slug": "toshkent-shahri"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000004",
          "name": "Shahar parki",
          "slug": "shahar-parki",
          "icon": "trees"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/amir-temur.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/amir-temur.jpg",
      "average_rating": 4.7,
      "review_count": 89,
      "best_time_to_visit": "Yil davomida",
      "entry_fee": null,
      "google_maps_url": "https://maps.google.com/?q=amir+temur+square",
      "yandex_maps_url": "https://yandex.uz/maps/?text=amir%20temur%20xiyoboni"
    }
  ],
  "regions": [
    {
      "id": "21000000-0000-0000-0000-000000000001",
      "name": "Samarqand viloyati",
      "slug": "samarqand-viloyati",
      "cover_image": "https://api.example.uz/media/regions/samarkand.jpg",
      "places_count": 42
    },
    {
      "id": "21000000-0000-0000-0000-000000000002",
      "name": "Xorazm viloyati",
      "slug": "xorazm-viloyati",
      "cover_image": "https://api.example.uz/media/regions/khorezm.jpg",
      "places_count": 18
    }
  ],
  "categories": [
    {
      "id": "31000000-0000-0000-0000-000000000001",
      "name": "Tarixiy obida",
      "slug": "tarixiy-obida",
      "icon": "landmark",
      "count": 88
    },
    {
      "id": "31000000-0000-0000-0000-000000000002",
      "name": "Ziyoratgoh",
      "slug": "ziyoratgoh",
      "icon": "mosque",
      "count": 95
    }
  ]
}
```

## 2. Barcha joylar sahifasi

### Request

```http
GET /api/v1/places/?page=1&page_size=12 HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "count": 320,
  "next": "https://api.example.uz/api/v1/places/?page=2&page_size=12",
  "previous": null,
  "results": [
    {
      "id": "11000000-0000-0000-0000-000000000001",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl va Samarqandning eng mashhur ramzlaridan biri.",
      "district": "Samarqand shahri",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000001",
          "name": "Tarixiy obida",
          "slug": "tarixiy-obida",
          "icon": "landmark"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/registon.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/?q=registon",
      "yandex_maps_url": "https://yandex.uz/maps/?text=registon"
    },
    {
      "id": "11000000-0000-0000-0000-000000000003",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "tagline": "Samarqanddagi muqaddas ziyorat maskani",
      "short_description": "Islom olamidagi muhim ziyorat joylaridan biri.",
      "district": "Payariq tumani",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000002",
          "name": "Ziyoratgoh",
          "slug": "ziyoratgoh",
          "icon": "mosque"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/imom-buxoriy.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/imom-buxoriy.jpg",
      "average_rating": 4.8,
      "review_count": 128,
      "best_time_to_visit": "Mart - May, Sentyabr - Noyabr",
      "entry_fee": null,
      "google_maps_url": "https://maps.google.com/?q=imam+bukhari+complex",
      "yandex_maps_url": "https://yandex.uz/maps/?text=imom%20buxoriy"
    }
  ]
}
```

## 3. Turistik joylar sahifasi

### Request

```http
GET /api/v1/places/?destination_type=tourist&page=1&page_size=12 HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "count": 225,
  "next": "https://api.example.uz/api/v1/places/?destination_type=tourist&page=2&page_size=12",
  "previous": null,
  "results": [
    {
      "id": "11000000-0000-0000-0000-000000000001",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl va Samarqandning eng mashhur ramzlaridan biri.",
      "district": "Samarqand shahri",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000001",
          "name": "Tarixiy obida",
          "slug": "tarixiy-obida",
          "icon": "landmark"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/registon.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/?q=registon",
      "yandex_maps_url": "https://yandex.uz/maps/?text=registon"
    }
  ]
}
```

## 4. Ziyoratgohlar sahifasi

### Request

```http
GET /api/v1/places/?destination_type=pilgrimage&page=1&page_size=12 HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "count": 95,
  "next": "https://api.example.uz/api/v1/places/?destination_type=pilgrimage&page=2&page_size=12",
  "previous": null,
  "results": [
    {
      "id": "11000000-0000-0000-0000-000000000003",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "tagline": "Samarqanddagi muqaddas ziyorat maskani",
      "short_description": "Islom olamidagi muhim ziyorat joylaridan biri.",
      "district": "Payariq tumani",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000002",
          "name": "Ziyoratgoh",
          "slug": "ziyoratgoh",
          "icon": "mosque"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/imom-buxoriy.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/imom-buxoriy.jpg",
      "average_rating": 4.8,
      "review_count": 128,
      "best_time_to_visit": "Mart - May, Sentyabr - Noyabr",
      "entry_fee": null,
      "google_maps_url": "https://maps.google.com/?q=imam+bukhari+complex",
      "yandex_maps_url": "https://yandex.uz/maps/?text=imom%20buxoriy"
    },
    {
      "id": "11000000-0000-0000-0000-000000000004",
      "name": "Bahouddin Naqshband majmuasi",
      "slug": "bahouddin-naqshband-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "tagline": "Buxorodagi mashhur ziyorat maskani",
      "short_description": "Naqshbandiya tariqati asoschisiga bag'ishlangan muqaddas maskan.",
      "district": "Buxoro tumani",
      "region": {
        "id": "21000000-0000-0000-0000-000000000003",
        "name": "Buxoro viloyati",
        "slug": "buxoro-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000002",
          "name": "Ziyoratgoh",
          "slug": "ziyoratgoh",
          "icon": "mosque"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/naqshband.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/naqshband.jpg",
      "average_rating": 4.9,
      "review_count": 166,
      "best_time_to_visit": "Yil davomida",
      "entry_fee": null,
      "google_maps_url": "https://maps.google.com/?q=bahouddin+naqshband",
      "yandex_maps_url": "https://yandex.uz/maps/?text=bahouddin%20naqshband"
    }
  ]
}
```

## 5. Region bo'yicha sahifa

### Request

```http
GET /api/v1/places/?region=samarqand-viloyati&page=1&page_size=12 HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "count": 42,
  "next": "https://api.example.uz/api/v1/places/?region=samarqand-viloyati&page=2&page_size=12",
  "previous": null,
  "results": [
    {
      "id": "11000000-0000-0000-0000-000000000001",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl va Samarqandning eng mashhur ramzlaridan biri.",
      "district": "Samarqand shahri",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000001",
          "name": "Tarixiy obida",
          "slug": "tarixiy-obida",
          "icon": "landmark"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/registon.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/?q=registon",
      "yandex_maps_url": "https://yandex.uz/maps/?text=registon"
    },
    {
      "id": "11000000-0000-0000-0000-000000000003",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "tagline": "Samarqanddagi muqaddas ziyorat maskani",
      "short_description": "Islom olamidagi muhim ziyorat joylaridan biri.",
      "district": "Payariq tumani",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000002",
          "name": "Ziyoratgoh",
          "slug": "ziyoratgoh",
          "icon": "mosque"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/imom-buxoriy.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/imom-buxoriy.jpg",
      "average_rating": 4.8,
      "review_count": 128,
      "best_time_to_visit": "Mart - May, Sentyabr - Noyabr",
      "entry_fee": null,
      "google_maps_url": "https://maps.google.com/?q=imam+bukhari+complex",
      "yandex_maps_url": "https://yandex.uz/maps/?text=imom%20buxoriy"
    }
  ]
}
```

## 6. Joy detail sahifasi

### Request

```http
GET /api/v1/places/imom-buxoriy-majmuasi/ HTTP/1.1
Host: api.example.uz
Accept: application/json
```

## 7. Joy detail ichidagi yo'nalish sahifasi

### Request

```http
GET /api/v1/places/imom-buxoriy-majmuasi/routes/ HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "destination": {
    "id": "11000000-0000-0000-0000-000000000003",
    "name": "Imom Buxoriy majmuasi",
    "slug": "imom-buxoriy-majmuasi"
  },
  "results": [
    {
      "id": "61000000-0000-0000-0000-000000000001",
      "title": "Samarqand shahridan mashinada",
      "transport_type": "car",
      "transport_type_label": "Mashina",
      "starting_point": "Samarqand shahri markazi",
      "route_description": "M37 yo'li orqali Payariq tomon harakat qilinadi, yo'l bo'ylab ko'rsatkichlar mavjud.",
      "distance_km": 28.5,
      "duration_text": "35 daqiqa",
      "map_url": "https://maps.google.com/?saddr=samarkand&daddr=imam+bukhari+complex",
      "notes": "Dam olish kunlari yo'lovchilar soni ko'p bo'lishi mumkin."
    },
    {
      "id": "61000000-0000-0000-0000-000000000002",
      "title": "Samarqand shahridan avtobusda",
      "transport_type": "bus",
      "transport_type_label": "Avtobus",
      "starting_point": "Samarqand avtovokzali",
      "route_description": "Payariq yo'nalishidagi avtobus yoki marshrutkalardan foydalaniladi.",
      "distance_km": 30.0,
      "duration_text": "50 daqiqa",
      "map_url": "",
      "notes": "Avtobus qatnov vaqtini mahalliy manbadan tekshirish tavsiya etiladi."
    }
  ]
}
```

## 8. Xarita sahifasi

### Request

```http
GET /api/v1/map/places/?destination_type=pilgrimage HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "results": [
    {
      "id": "11000000-0000-0000-0000-000000000003",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "latitude": 39.775412,
      "longitude": 66.921573,
      "region_name": "Samarqand viloyati",
      "cover_image": "https://api.example.uz/media/destinations/covers/imom-buxoriy.jpg",
      "google_maps_url": "https://maps.google.com/?q=imam+bukhari+complex"
    },
    {
      "id": "11000000-0000-0000-0000-000000000004",
      "name": "Bahouddin Naqshband majmuasi",
      "slug": "bahouddin-naqshband-majmuasi",
      "destination_type": "pilgrimage",
      "destination_type_label": "Ziyoratgoh",
      "latitude": 39.743211,
      "longitude": 64.451672,
      "region_name": "Buxoro viloyati",
      "cover_image": "https://api.example.uz/media/destinations/covers/naqshband.jpg",
      "google_maps_url": "https://maps.google.com/?q=bahouddin+naqshband"
    }
  ]
}
```

## 9. FAQ sahifasi

### Request

```http
GET /api/v1/faqs/?destination_slug=imom-buxoriy-majmuasi HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "81000000-0000-0000-0000-000000000001",
      "question": "Bu joyga kirish pullikmi?",
      "answer": "Hozircha kirish bepul, ayrim xizmatlar pullik bo'lishi mumkin.",
      "destination": {
        "id": "11000000-0000-0000-0000-000000000003",
        "name": "Imom Buxoriy majmuasi",
        "slug": "imom-buxoriy-majmuasi"
      }
    },
    {
      "id": "81000000-0000-0000-0000-000000000002",
      "question": "Mashina qo'yish joyi bormi?",
      "answer": "Ha, majmua atrofida avtoturargoh mavjud.",
      "destination": {
        "id": "11000000-0000-0000-0000-000000000003",
        "name": "Imom Buxoriy majmuasi",
        "slug": "imom-buxoriy-majmuasi"
      }
    }
  ]
}
```

## 10. Search suggest

### Request

```http
GET /api/v1/search/suggestions/?q=imom HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

```json
{
  "query": "imom",
  "results": [
    {
      "type": "destination",
      "id": "11000000-0000-0000-0000-000000000003",
      "name": "Imom Buxoriy majmuasi",
      "slug": "imom-buxoriy-majmuasi",
      "destination_type": "pilgrimage",
      "region_name": "Samarqand viloyati",
      "cover_image": "https://api.example.uz/media/destinations/covers/imom-buxoriy.jpg"
    },
    {
      "type": "destination",
      "id": "11000000-0000-0000-0000-000000000005",
      "name": "Imom Moturidiy majmuasi",
      "slug": "imom-moturidiy-majmuasi",
      "destination_type": "pilgrimage",
      "region_name": "Samarqand viloyati",
      "cover_image": "https://api.example.uz/media/destinations/covers/imom-moturidiy.jpg"
    }
  ]
}
```

## 11. Filter metadata

### Request

```http
GET /api/v1/meta/filters/ HTTP/1.1
Host: api.example.uz
Accept: application/json
```

### Full example response

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
    },
    {
      "value": "mixed",
      "label": "Turistik va ziyorat",
      "count": 0
    }
  ],
  "regions": [
    {
      "id": "21000000-0000-0000-0000-000000000001",
      "name": "Samarqand viloyati",
      "slug": "samarqand-viloyati",
      "count": 42
    },
    {
      "id": "21000000-0000-0000-0000-000000000003",
      "name": "Buxoro viloyati",
      "slug": "buxoro-viloyati",
      "count": 31
    }
  ],
  "categories": [
    {
      "id": "31000000-0000-0000-0000-000000000001",
      "name": "Tarixiy obida",
      "slug": "tarixiy-obida",
      "icon": "landmark",
      "count": 88
    },
    {
      "id": "31000000-0000-0000-0000-000000000002",
      "name": "Ziyoratgoh",
      "slug": "ziyoratgoh",
      "icon": "mosque",
      "count": 95
    }
  ]
}
```

## 12. Frontend uchun qisqa mapping

- `home page`: `/api/v1/home/`
- `places page`: `/api/v1/places/`
- `tourist page`: `/api/v1/places/?destination_type=tourist`
- `pilgrimage page`: `/api/v1/places/?destination_type=pilgrimage`
- `region page`: `/api/v1/places/?region={region_slug}`
- `place detail page`: `/api/v1/places/{slug}/`
- `routes block`: `/api/v1/places/{slug}/routes/`
- `map page`: `/api/v1/map/places/`
- `faq page`: `/api/v1/faqs/`
- `header search`: `/api/v1/search/suggestions/?q={text}`
- `filter sidebar`: `/api/v1/meta/filters/`

### Full example response

```json
{
  "id": "11000000-0000-0000-0000-000000000003",
  "name": "Imom Buxoriy majmuasi",
  "slug": "imom-buxoriy-majmuasi",
  "destination_type": "pilgrimage",
  "destination_type_label": "Ziyoratgoh",
  "tagline": "Samarqanddagi muqaddas ziyorat maskani",
  "short_description": "Islom olamidagi muhim ziyorat joylaridan biri.",
  "overview": "Majmua Imom al-Buxoriy xotirasiga bag'ishlangan bo'lib, ziyoratchilar va sayyohlar uchun muhim maskan hisoblanadi.",
  "history": "Bu hudud tarixiy manbalarda buyuk muhaddis Imom Buxoriy bilan bog'liq maskan sifatida tilga olinadi. Keyingi yillarda majmua zamonaviy ko'rinishda qayta ta'mirlangan.",
  "how_to_get_there": "Samarqand shahridan avtomobil orqali Payariq tumani tomon boriladi. Avtobus va taksi xizmatlari ham mavjud.",
  "visiting_hours": "08:00 - 20:00",
  "address": "Samarqand viloyati, Payariq tumani, Imom Buxoriy majmuasi",
  "district": "Payariq tumani",
  "landmark": "Asosiy katta masjid yaqinida",
  "latitude": 39.775412,
  "longitude": 66.921573,
  "best_time_to_visit": "Mart - May, Sentyabr - Noyabr",
  "recommended_visit_duration": "1-2 soat",
  "entry_fee": null,
  "ticket_notes": "Kirish bepul",
  "contact_phone": "+998662345678",
  "official_website": "https://example.uz/imom-buxoriy",
  "google_maps_url": "https://maps.google.com/?q=imam+bukhari+complex",
  "yandex_maps_url": "https://yandex.uz/maps/?text=imom%20buxoriy",
  "hero_image": "https://api.example.uz/media/destinations/heroes/imom-buxoriy.jpg",
  "cover_image": "https://api.example.uz/media/destinations/covers/imom-buxoriy.jpg",
  "average_rating": 4.8,
  "review_count": 128,
  "region": {
    "id": "21000000-0000-0000-0000-000000000001",
    "name": "Samarqand viloyati",
    "slug": "samarqand-viloyati"
  },
  "categories": [
    {
      "id": "31000000-0000-0000-0000-000000000002",
      "name": "Ziyoratgoh",
      "slug": "ziyoratgoh",
      "icon": "mosque"
    }
  ],
  "amenities": [
    {
      "id": "41000000-0000-0000-0000-000000000001",
      "name": "Avtoturargoh",
      "slug": "avtoturargoh",
      "icon": "car"
    },
    {
      "id": "41000000-0000-0000-0000-000000000002",
      "name": "Tahoratxona",
      "slug": "tahoratxona",
      "icon": "droplets"
    }
  ],
  "gallery": [
    {
      "id": "51000000-0000-0000-0000-000000000001",
      "image": "https://api.example.uz/media/destinations/gallery/imom-buxoriy-1.jpg",
      "alt_text": "Majmuaning asosiy kirish qismi",
      "caption": "Asosiy kirish qismi",
      "is_cover": true,
      "sort_order": 0
    }
  ],
  "nearby_places": [
    {
      "id": "11000000-0000-0000-0000-000000000001",
      "name": "Registon maydoni",
      "slug": "registon-maydoni",
      "destination_type": "tourist",
      "destination_type_label": "Turistik joy",
      "tagline": "Samarqandning yuragi",
      "short_description": "Tarixiy me'moriy ansambl va Samarqandning eng mashhur ramzlaridan biri.",
      "district": "Samarqand shahri",
      "region": {
        "id": "21000000-0000-0000-0000-000000000001",
        "name": "Samarqand viloyati",
        "slug": "samarqand-viloyati"
      },
      "categories": [
        {
          "id": "31000000-0000-0000-0000-000000000001",
          "name": "Tarixiy obida",
          "slug": "tarixiy-obida",
          "icon": "landmark"
        }
      ],
      "cover_image": "https://api.example.uz/media/destinations/covers/registon.jpg",
      "hero_image": "https://api.example.uz/media/destinations/heroes/registon.jpg",
      "average_rating": 4.9,
      "review_count": 412,
      "best_time_to_visit": "Aprel - Iyun",
      "entry_fee": 50000.0,
      "google_maps_url": "https://maps.google.com/?q=registon",
      "yandex_maps_url": "https://yandex.uz/maps/?text=registon"
    }
  ],
  "routes": [
    {
      "id": "61000000-0000-0000-0000-000000000001",
      "title": "Samarqand shahridan mashinada",
      "transport_type": "car",
      "transport_type_label": "Mashina",
      "starting_point": "Samarqand shahri markazi",
      "route_description": "M37 yo'li orqali Payariq tomon harakat qilinadi, yo'l bo'ylab ko'rsatkichlar mavjud.",
      "distance_km": 28.5,
      "duration_text": "35 daqiqa",
      "map_url": "https://maps.google.com/?saddr=samarkand&daddr=imam+bukhari+complex",
      "notes": "Dam olish kunlari yo'lovchilar soni ko'p bo'lishi mumkin."
    }
  ],
  "reviews_preview": [
    {
      "id": "71000000-0000-0000-0000-000000000001",
      "author_name": "Aziza",
      "rating": 5,
      "title": "Juda fayzli joy",
      "body": "Oilaviy tashrif uchun juda qulay va tartibli joy ekan.",
      "visited_at": "2026-02-12"
    }
  ],
  "faqs_preview": [
    {
      "id": "81000000-0000-0000-0000-000000000001",
      "question": "Bu joyga kirish pullikmi?",
      "answer": "Hozircha kirish bepul, ayrim xizmatlar pullik bo'lishi mumkin."
    }
  ]
}
```
