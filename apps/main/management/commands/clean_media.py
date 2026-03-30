import os
import shutil
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.main.models import Destination, DestinationImage

class Command(BaseCommand):
    help = 'Xato yuklangan media fayllarni butunlay tozalaydi va DB ni tozalovdan o\'tkazadi.'

    def handle(self, *args, **options):
        self.stdout.write("Barcha tasvir ma'lumotlari buzib yuborilmoqda...")
        DestinationImage.objects.all().delete()
        
        for d in Destination.objects.all():
            d.cover_image = None
            d.hero_image = None
            d.save()
            
        dest_media_path = os.path.join(settings.MEDIA_ROOT, 'destinations')
        if os.path.exists(dest_media_path):
            shutil.rmtree(dest_media_path)
            
        self.stdout.write(self.style.SUCCESS("Media va Bazadagi barcha xato rasmlar qirib tashlandi!"))
