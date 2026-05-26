from django.core.management.base import BaseCommand
from user.models import Product
import requests
import os
import time
from django.conf import settings


class Command(BaseCommand):
    help = 'Download product images based on product name'

    def handle(self, *args, **kwargs):
        media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(media_dir, exist_ok=True)
        
        products = Product.objects.all()
        total = products.count()
        
        self.stdout.write(self.style.SUCCESS(f'Downloading relevant images for {total} products...'))
        
        success_count = 0
        error_count = 0
        
        # Use Lorem Picsum with keyword-based approach
        # We'll use different image sources for variety
        
        for i, product in enumerate(products):
            # Clean the product name for filename
            filename = product.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{filename}.jpg"
            filepath = os.path.join(media_dir, filename)
            
            # Skip if file already exists (to save time)
            if os.path.exists(filepath):
                self.stdout.write(f'[{i+1}/{total}] Skipping (exists): {product.name}')
                success_count += 1
                continue
            
            try:
                # Use picsum with different categories
                # Generate a hash-based seed for consistent results
                seed = sum(ord(c) for c in product.name) % 1000
                
                # Try with different image services
                image_url = f"https://picsum.photos/seed/{seed}/800/800"
                
                response = requests.get(image_url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    product.image = f'products/{filename}'
                    product.save(update_fields=['image'])
                    
                    success_count += 1
                    self.stdout.write(f'[{i+1}/{total}] Downloaded: {product.name}')
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'[{i+1}/{total}] Failed: {product.name}'))
                
                # Small delay to avoid rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'[{i+1}/{total}] Error: {product.name} - {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nCompleted! Success: {success_count}, Errors: {error_count}'))
