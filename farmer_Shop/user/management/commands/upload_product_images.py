from django.core.management.base import BaseCommand
from user.models import Product, Category
import os
import shutil
from django.conf import settings


class Command(BaseCommand):
    help = 'Upload product images from static/images/products to product table'

    def handle(self, *args, **kwargs):
        # Paths
        static_images_dir = os.path.join(settings.BASE_DIR, 'user', 'static', 'images', 'products')
        media_products_dir = os.path.join(settings.BASE_DIR, 'media', 'products')
        
        # Create media/products directory if it doesn't exist
        os.makedirs(media_products_dir, exist_ok=True)
        
        # Get all products
        products = Product.objects.all()
        
        # Create mapping of product name to image filename
        # The static images use spaces like "Fresh Tomato.jpg" 
        # But product names may vary like "Fresh Tomato" or "Tomato"
        
        # First, let's see what images exist in static
        static_images = os.listdir(static_images_dir)
        self.stdout.write(f"Found {len(static_images)} images in static/products")
        
        # Create a mapping of normalized names
        image_mapping = {}
        for img in static_images:
            if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                # Remove extension to get the base name
                base_name = os.path.splitext(img)[0].lower()
                image_mapping[base_name] = img
        
        # Also check media directory for existing images
        media_images = os.listdir(media_products_dir) if os.path.exists(media_products_dir) else []
        media_image_mapping = {}
        for img in media_images:
            if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                base_name = os.path.splitext(img)[0].lower().replace('_', ' ')
                media_image_mapping[base_name] = img
        
        updated_count = 0
        
        for product in products:
            product_name_lower = product.name.lower()
            
            # Try to find matching image
            matched_image = None
            
            # 1. Check direct match in static images
            for base_name, img_file in image_mapping.items():
                if product_name_lower == base_name or product_name_lower.replace(' ', '_') == base_name:
                    matched_image = img_file
                    break
            
            # 2. Check partial match (e.g., "Fresh Tomato" matches "Tomato")
            if not matched_image:
                for base_name, img_file in image_mapping.items():
                    if base_name in product_name_lower or product_name_lower in base_name:
                        matched_image = img_file
                        break
            
            # 3. Check media directory
            if not matched_image:
                for base_name, img_file in media_image_mapping.items():
                    if product_name_lower == base_name or product_name_lower.replace(' ', '_') == base_name:
                        matched_image = img_file
                        break
            
            # 4. Check partial match in media
            if not matched_image:
                for base_name, img_file in media_image_mapping.items():
                    if base_name in product_name_lower or product_name_lower in base_name:
                        matched_image = img_file
                        break
            
            if matched_image:
                # Determine source and destination paths
                if matched_image in image_mapping:
                    source_path = os.path.join(static_images_dir, matched_image)
                else:
                    source_path = os.path.join(media_products_dir, matched_image)
                
                dest_filename = matched_image.replace(' ', '_')
                dest_path = os.path.join(media_products_dir, dest_filename)
                
                # Copy file if it doesn't exist in media
                if not os.path.exists(dest_path):
                    try:
                        shutil.copy2(source_path, dest_path)
                        self.stdout.write(f"Copied: {matched_image} -> {dest_filename}")
                    except Exception as e:
                        self.stderr.write(f"Error copying {matched_image}: {e}")
                
                # Update product image field (store relative path from media)
                product.image = f'products/{dest_filename}'
                product.save(update_fields=['image'])
                updated_count += 1
                self.stdout.write(f"Updated product '{product.name}' with image '{dest_filename}'")
            else:
                self.stdout.write(f"No image found for product: {product.name}")
        
        self.stdout.write(self.style.SUCCESS(f"Total products updated with images: {updated_count}"))
