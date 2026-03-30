import os
import time
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.main.models import Destination, DestinationImage

class Command(BaseCommand):
    help = 'Destinations jadvalidagi har bir joyga Wikimedia Thumbnails orqali limitga tushmasdan aniq rasmlarni tortadi.'

    def get_commons_thumbnails(self, query_string, limit=12):
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": query_string,
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": "800", # Asl emas kichraytirilgan original (429 xatosi bermasligi uchun)
            "format": "json"
        }
        headers = {'User-Agent': 'TurizmAppBot/2.0 (wiki_test@example.com)'}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                pages = response.json().get("query", {}).get("pages", {})
                urls = []
                for _, info in pages.items():
                    if "imageinfo" in info:
                        img_info = info["imageinfo"][0]
                        thumb_url = img_info.get("thumburl", img_info.get("url"))
                        if thumb_url and thumb_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                            urls.append((thumb_url, img_info.get("descriptionshorturl", "")))
                return list(set(urls))[:limit] 
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"API Error fetching {query_string}: {e}"))
        return []

    def fetch_image(self, url, filename):
        if not url: return None
        try:
            time.sleep(1)
            headers = {'User-Agent': 'TurizmAppBot/2.0 (wiki_test@example.com)'}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return ContentFile(response.content, name=filename)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Download Error ({filename}): {e}"))
        return None

    def handle(self, *args, **options):
        destinations = Destination.objects.all()
        total = destinations.count()
        self.stdout.write(f"Jami joylar: {total} ta topildi.")

        for index, dest in enumerate(destinations, 1):
            search_query = dest.name_en # Masalan: "Registan Square", "Charvak Reservoir"
            
            self.stdout.write(self.style.SUCCESS(f"\n=> [{index}/{total}] Ishlanmoqda: {dest.name_uz} | Qidiruv: '{search_query}'"))
            
            image_data = self.get_commons_thumbnails(search_query, limit=12)
            self.stdout.write(f"  {len(image_data)} xil thumb (.jpg) havola topildi...")

            if not image_data:
                # Agar to'liq nomiga topolmasa, birinchi so'ziga (masalan: Ichan-Kala) izlab ko'ramiz
                fallback_query = search_query.split()[0]
                image_data = self.get_commons_thumbnails(fallback_query, limit=12)
                self.stdout.write(f"  {len(image_data)} xil havola (Zahira izlash '{fallback_query}')")
                if not image_data:
                    continue
                
            image_urls = [item[0] for item in image_data]

            # 2. Asosiy va cover rasmni yopamiz 
            if not dest.hero_image and len(image_urls) > 0:
                h_url = image_urls.pop(0)
                file = self.fetch_image(h_url, f"hero_{dest.slug}.jpg")
                if file: dest.hero_image.save(f"hero_{dest.slug}.jpg", file)
                
            if not dest.cover_image and len(image_urls) > 0:
                c_url = image_urls.pop(0)
                file = self.fetch_image(c_url, f"cover_{dest.slug}.jpg")
                if file: dest.cover_image.save(f"cover_{dest.slug}.jpg", file)

            dest.save()

            # 3. Galereya
            count = 1
            added = 0
            for img_url in image_urls[:10]:
                file_obj = self.fetch_image(img_url, f"gallery_{dest.slug}_{count}.jpg")
                if file_obj:
                    DestinationImage.objects.create(
                        destination=dest,
                        image=file_obj,
                        alt_text_uz=f"{dest.name_uz} haqiqiy tasviri ({count})",
                        alt_text_ru=f"Реальный вид {dest.name_ru} ({count})",
                        alt_text_en=f"Real view of {dest.name_en} ({count})",
                        is_cover=False,
                        sort_order=count
                    )
                    added += 1
                count += 1
            self.stdout.write(self.style.SUCCESS(f"  Galereya rasmlari {added} xil turli mualliflardan bazaga yozildi!"))

        self.stdout.write(self.style.SUCCESS('\nBarcha jarayon to\'la tugatildi!'))
