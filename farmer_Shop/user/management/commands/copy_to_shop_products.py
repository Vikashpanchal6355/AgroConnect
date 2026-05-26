from django.core.management.base import BaseCommand
from user.models import Product
import os
import shutil
from django.conf import settings


class Command(BaseCommand):
    help = 'Copy product images from products folder to shop-products folder matching product names'

    def handle(self, *args, **kwargs):
        # Paths
        products_source_dir = os.path.join(settings.BASE_DIR, 'user', 'static', 'images', 'products')
        shop_products_dest_dir = os.path.join(settings.BASE_DIR, 'user', 'static', 'images', 'shop-products')
        
        # Create shop-products directory if it doesn't exist
        os.makedirs(shop_products_dest_dir, exist_ok=True)
        
        # Get all products from database
        products = Product.objects.all()
        
        # Get all images from source directory
        source_images = os.listdir(products_source_dir)
        
        # Create mapping of normalized image names (without extension, lowercase)
        image_mapping = {}
        for img in source_images:
            if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                # Get the base name without extension
                base_name = os.path.splitext(img)[0].lower()
                # Keep original extension
                ext = os.path.splitext(img)[1].lower()
                image_mapping[base_name] = (img, ext)
        
        copied_count = 0
        not_found = []
        
        for product in products:
            product_name_lower = product.name.lower()
            matched_image = None
            matched_ext = None
            
            # 1. Try direct match first
            if product_name_lower in image_mapping:
                matched_image = image_mapping[product_name_lower][0]
                matched_ext = image_mapping[product_name_lower][1]
            
            # 2. Try with spaces replaced by underscores
            if not matched_image:
                product_name_underscore = product_name_lower.replace(' ', '_')
                if product_name_underscore in image_mapping:
                    matched_image = image_mapping[product_name_underscore][0]
                    matched_ext = image_mapping[product_name_underscore][1]
            
            # 3. Try partial match (e.g., "Fresh Tomato" matches "Fresh Tomato.jpg")
            if not matched_image:
                for img_base, (img_file, ext) in image_mapping.items():
                    if product_name_lower == img_base or product_name_lower.replace(' ', '_') == img_base:
                        matched_image = img_file
                        matched_ext = ext
                        break
            
            if matched_image:
                # Create destination filename with product name
                dest_filename = f"{product.name}{matched_ext}"
                dest_path = os.path.join(shop_products_dest_dir, dest_filename)
                source_path = os.path.join(products_source_dir, matched_image)
                
                # Copy the file
                try:
                    shutil.copy2(source_path, dest_path)
                    copied_count += 1
                    self.stdout.write(f"Copied: {matched_image} -> {dest_filename}")
                except Exception as e:
                    self.stderr.write(f"Error copying {matched_image}: {e}")
            else:
                not_found.append(product.name)
                self.stdout.write(f"No image found for product: {product.name}")
        
        self.stdout.write(self.style.SUCCESS(f"\nTotal images copied: {copied_count}"))
        if not_found:
            self.stdout.write(self.style.WARNING(f"Products without images ({len(not_found)}): {', '.join(not_found)}"))
