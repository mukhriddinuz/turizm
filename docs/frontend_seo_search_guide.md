# SEO va Qidiruv Integratsiyasi (Frontend uchun)

## 1) Backendda tayyorlangan endpointlar

- `GET /api/v1/seo/meta/`
  - Query paramlar:
    - `page_type`: `home | about | culture | place | route | region | search`
    - `lang`: `uz | ru | en` (default: `uz`)
    - `slug`: `place` yoki `region` uchun
    - `id`: `route` uchun UUID
    - `q`: `search` uchun qidiruv matni
- `GET /api/v1/search/suggestions/?q=...&limit=...`
  - Header qidiruv uchun tezkor takliflar (relevance + cache).
- `GET /api/v1/search/global/?q=...&limit=...`
  - To'liq qidiruv: `destinations`, `routes`, `regions`.
- `GET /api/v1/about/`
  - About bo'limi: `title`, `description`, `videos[]`, `images`.
  - `videos[]` elementi: `id`, `title`, `url`, `thumbnail`, `sort_order`.
  - `video_url` legacy maydon sifatida saqlangan (orqaga moslik uchun).
- `GET /api/v1/culture/`
  - Madaniyat kartochkalari (`results[]`).
- `GET /robots.txt`
- `GET /sitemap.xml`


## 2) Frontendda SEO bo'yicha majburiy ishlar

## 2.1 Har bir page renderida `seo/meta` ni chaqirish

- Home:
  - `/api/v1/seo/meta/?page_type=home&lang=uz`
- About:
  - `/api/v1/seo/meta/?page_type=about&lang=uz`
- Culture:
  - `/api/v1/seo/meta/?page_type=culture&lang=uz`
- Place detail:
  - `/api/v1/seo/meta/?page_type=place&slug={slug}&lang=uz`
- Region detail:
  - `/api/v1/seo/meta/?page_type=region&slug={slug}&lang=uz`
- Route detail:
  - `/api/v1/seo/meta/?page_type=route&id={uuid}&lang=uz`
- Search page:
  - `/api/v1/seo/meta/?page_type=search&q={query}&lang=uz`

## 2.2 `<head>` ichida quyidagilarni set qiling

- `<title>`
- `<meta name="description">`
- `<meta name="keywords">`
- `<link rel="canonical">`
- `<meta name="robots">`
- Open Graph:
  - `og:title`, `og:description`, `og:type`, `og:url`, `og:image`
- Twitter:
  - `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`

## 2.3 JSON-LD ni inject qiling

- `seo/meta` javobidagi `structured_data` ni:
  - `<script type="application/ld+json">...</script>` ichiga yozing.

## 2.4 SSR/Prerender talabi

- SEO uchun muhim sahifalar server tarafda render bo'lishi kerak:
  - Home, About, Place detail, Region detail, Route detail.
- Agar SPA bo'lsa:
  - Prerender (yoki dynamic rendering) ishlating.


## 3) Qidiruv UX bo'yicha frontend vazifalari

## 3.1 Suggestions

- Inputga debounce qo'ying: `250-350ms`.
- So'rovni `q.length >= 2` bo'lganda yuboring.
- Endpoint:
  - `/api/v1/search/suggestions/?q={q}&limit=10`
- UI da ko'rsating:
  - `name`
  - `destination_type_label`
  - `region_name`
  - `cover_image`

## 3.2 Global search page

- Endpoint:
  - `/api/v1/search/global/?q={q}&limit=8`
- Response bo'limlari:
  - `results.destinations`
  - `results.routes`
  - `results.regions`
- Tablar bo'yicha ajrating: `Barchasi / Joylar / Yo'nalishlar / Hududlar`.

## 3.3 No-result va analytics

- `totals.all === 0` bo'lsa:
  - "Natija topilmadi" blokini ko'rsating.
- Qidiruv query'sini URLda saqlang (`/search?q=...`) - shareable URL uchun.


## 4) Router va URL qoidalari

- Place detail: `/places/{slug}`
- Region detail: `/regions/{slug}`
- Route detail: `/routes/{id}`
- Search: `/search?q={query}`
- About: `/about`
- Culture: `/culture`


## 5) Release oldidan checklist

- Har sahifada `title/description/canonical/robots` bor.
- `structured_data` script brauzerda bor.
- `robots.txt` ochiladi.
- `sitemap.xml` ochiladi.
- Search input debounce ishlaydi.
- Search URL query saqlanadi.
- Mobile va desktopda qidiruv dropdown to'g'ri ko'rinadi.
