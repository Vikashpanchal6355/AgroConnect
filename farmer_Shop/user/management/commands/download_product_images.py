from django.core.management.base import BaseCommand
from user.models import Product
import requests
import os
import hashlib
from django.conf import settings


class Command(BaseCommand):
    help = 'Download product images from Lorem Picsum'

    def handle(self, *args, **kwargs):
        # Get media directory
        media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        
        # Create directory if it doesn't exist
        os.makedirs(media_dir, exist_ok=True)
        
        # Get all products
        products = Product.objects.all()
        total = products.count()
        
        self.stdout.write(self.style.SUCCESS(f'Starting download for {total} products...'))
        
        # Image URLs for different categories (using Unsplash source for variety)
        # We'll use picsum.photos with unique seeds for each product
        
        success_count = 0
        error_count = 0
        
        for i, product in enumerate(products):
            # Generate a unique seed based on product name
            seed = int(hashlib.md5(product.name.encode()).hexdigest()[:8], 16) % 1000
            
            # Use picsum.photos for random images
            # Size 800x800 for good quality
            image_url = f"https://picsum.photos/seed/{seed}/800/800"
            
            # Create filename from product name
            filename = product.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{filename}.jpg"
            filepath = os.path.join(media_dir, filename)
            
            try:
                # Download the image
                response = requests.get(image_url, timeout=30)
                
                if response.status_code == 200:
                    # Save the image
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    # Update product image field (relative to media folder)
                    product.image = f'products/{filename}'
                    product.save()
                    
                    success_count += 1
                    self.stdout.write(f'[{i+1}/{total}] Downloaded: {product.name}')
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'[{i+1}/{total}] Failed: {product.name} - Status: {response.status_code}'))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'[{i+1}/{total}] Error downloading {product.name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nCompleted! Success: {success_count}, Errors: {error_count}'))
