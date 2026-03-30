import os
import time
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.main.models import Destination, DestinationImage

class Command(BaseCommand):
    help = 'Destinations jadvalidagi har bir joyga Flickr orqali aniq taglar yordamida rasmlarni olib keladi (Wikipedia va xavfsizlik cheklovlarini aylanib o\'tish).'

    def fetch_image(self, url, filename):
        if not url: return None
        try:
            time.sleep(1)
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
            if response.status_code == 200 and len(response.content) > 10000:  # Minimum 10KB to avoid error images
                return ContentFile(response.content, name=filename)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Download Error ({filename}): {e}"))
        return None

    def handle(self, *args, **options):
        # Qaysi obyekti qaysi kalitli so'zlari orqali ishonchli izlash (Flickr Tags)
        FLICKR_TAGS = {
            "registon-maydoni": "registan,samarkand,monument",
            "hazrati-imom-hastimom-majmuasi": "hastimom,tashkent,mosque",
            "amir-temur-xiyoboni": "amirtimur,square,tashkent",
            "chorvoq-suv-ombori": "charvak,reservoir,mountains",
            "ark-qalasi": "ark,fortress,bukhara",
            "bahouddin-naqshband-majmuasi": "bahauddin,naqshband,bukhara",
            "ichan-qala": "itchankala,khiva,architecture",
            "oqsaroy": "aksaray,shakhrisabz,palace",
            "ivsavitskiy-nomidagi-muzey": "savitsky,museum,nukus",
            "hakim-at-termiziy-majmuasi": "termizi,mausoleum,termez",
            "sarmishsoy-qoyatosh-suratlari": "sarmishsay,petroglyphs,navoi",
            "kalta-minor": "kaltaminor,khiva,minaret",
            "xudoyorxon-ordasi": "khudayarkhan,palace,kokand",
            "bobur-bogi": "babur,park,andijan",
            "zomin-milliy-bogi": "zaamin,nationalpark,mountains",
            "afsonalar-vodiysi-parki": "valleyoflegends,namangan,park",
            "sirdaryo-boyi-vohalari": "syrdarya,river,oasis",
            "imom-buxoriy-ziyoratgohi": "imambukhari,samarkand,mausoleum",
        }

        destinations = Destination.objects.all()
        total = destinations.count()
        self.stdout.write(f"Jami joylar: {total} ta topildi.")

        for index, dest in enumerate(destinations, 1):
            tags = FLICKR_TAGS.get(dest.slug)
            if not tags:
                self.stdout.write(self.style.WARNING(f"Tag topilmadi: slug={dest.slug}"))
                continue
            
            self.stdout.write(self.style.SUCCESS(f"\n=> [{index}/{total}] Ishlanmoqda: {dest.name_uz} | Tags: {tags}"))

            # Bosh (Cover & Hero) tasvirlarini to'ldirish
            if not dest.hero_image:
                file = self.fetch_image(f"https://loremflickr.com/1280/800/{tags}/all?lock=100", f"hero_{dest.slug}.jpg")
                if file: dest.hero_image.save(f"hero_{dest.slug}.jpg", file)
                
            if not dest.cover_image:
                file = self.fetch_image(f"https://loremflickr.com/800/600/{tags}/all?lock=101", f"cover_{dest.slug}.jpg")
                if file: dest.cover_image.save(f"cover_{dest.slug}.jpg", file)
            
            dest.save()

            # Qolgan 10 ta rasmni Galereyaga qo'shish
            self.stdout.write("  Yangi galereya rasmlari qo'shilyapti...")
            DestinationImage.objects.filter(destination=dest).delete()

            success_count = 0
            for i in range(1, 11):
                url = f"https://loremflickr.com/800/600/{tags}/all?lock={i}"
                file_obj = self.fetch_image(url, f"gallery_{dest.slug}_{i}.jpg")
                if file_obj:
                    DestinationImage.objects.create(
                        destination=dest,
                        image=file_obj,
                        alt_text_uz=f"{dest.name_uz} manzarasi {i}",
                        alt_text_ru=f"Вид на {dest.name_ru} {i}",
                        alt_text_en=f"View of {dest.name_en} {i}",
                        is_cover=False,
                        sort_order=i
                    )
                    success_count += 1
            self.stdout.write(self.style.SUCCESS(f"  Galereya rasmlari bazaga tushdi: {success_count} ta!"))

        self.stdout.write(self.style.SUCCESS('\nBarcha jarayon to\'la tugatildi! Media qayta to\'ldirildi.'))
