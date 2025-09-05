"""
Image Processing Service - Single Responsibility Principle
Handles all image manipulation operations with folder batching support
"""

from PIL import Image
import os
import math
import random

class ImageProcessor:
    """Handles image processing operations"""
    
    def __init__(self):
        """Initialize image processor"""
        self.supported_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    def get_image_files(self, folder_path):
        """
        Get all supported image files from folder
        
        Args:
            folder_path (str): Path to folder containing images
            
        Returns:
            list: Sorted list of image file paths
        """
        if not os.path.exists(folder_path):
            return []
        
        image_files = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.supported_extensions:
                    image_files.append(file_path)
        
        return sorted(image_files)  # Deterministic order
    
    def aspect_fit_contain(self, image, target_size):
        """
        Resize image to fit within target size while maintaining aspect ratio
        
        Args:
            image (PIL.Image): Source image
            target_size (tuple): Target (width, height)
            
        Returns:
            PIL.Image: Resized image
        """
        # Calculate scaling factor to fit within target size
        width_ratio = target_size[0] / image.width
        height_ratio = target_size[1] / image.height
        scale_factor = min(width_ratio, height_ratio)
        
        # Calculate new size
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)
        
        # Resize image
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def center_image_on_background(self, icon, background, target_size):
        """
        Center icon on background at target size
        
        Args:
            icon (PIL.Image): Icon image (already resized)
            background (PIL.Image): Background image
            target_size (tuple): Target size for final image
            
        Returns:
            PIL.Image: Composed image
        """
        # Resize background to target size
        bg_resized = background.resize(target_size, Image.Resampling.LANCZOS)
        
        # Create final image
        result = Image.new('RGBA', target_size, (0, 0, 0, 0))
        
        # Paste background
        result.paste(bg_resized, (0, 0))
        
        # Calculate center position for icon
        x_offset = (target_size[0] - icon.width) // 2
        y_offset = (target_size[1] - icon.height) // 2
        
        # Paste icon with alpha compositing
        if icon.mode == 'RGBA':
            result.paste(icon, (x_offset, y_offset), icon)
        else:
            result.paste(icon, (x_offset, y_offset))
        
        return result
    
    def batch_merge_icons_with_backgrounds(self, icon_folder, bg_folder, output_folder, 
                                         target_size, save_individual=False, use_versioning=False):
        """
        Batch merge icons with random backgrounds
        
        Args:
            icon_folder (str): Path to icon folder
            bg_folder (str): Path to background folder
            output_folder (str): Path to output folder (for individual files)
            target_size (tuple): Target size (width, height)
            save_individual (bool): Whether to save individual merged images
            use_versioning (bool): Whether to add version numbers for existing files
            
        Returns:
            tuple: (list_of_merged_images, folder_base_name)
        """
        icon_files = self.get_image_files(icon_folder)
        bg_files = self.get_image_files(bg_folder)
        
        if not icon_files:
            raise ValueError("No icon files found in the specified folder")
        if not bg_files:
            raise ValueError("No background files found in the specified folder")
        
        merged_images = []
        
        # Get folder base name for spritesheet naming
        folder_base_name = os.path.basename(icon_folder.rstrip(os.sep))
        
        print(f"Processing {len(icon_files)} icons from '{folder_base_name}' folder...")
        
        for i, icon_path in enumerate(icon_files):
            try:
                # Load icon and convert to RGBA
                icon = Image.open(icon_path).convert('RGBA')
                
                # Pick random background
                bg_path = random.choice(bg_files)
                background = Image.open(bg_path).convert('RGBA')
                
                # Resize icon to fit within target size
                icon_resized = self.aspect_fit_contain(icon, target_size)
                
                # Center icon on background
                merged = self.center_image_on_background(icon_resized, background, target_size)
                
                # Save individual file if requested
                if save_individual and output_folder:
                    os.makedirs(output_folder, exist_ok=True)
                    icon_stem = os.path.splitext(os.path.basename(icon_path))[0]
                    
                    if use_versioning:
                        # Find unique filename with versioning
                        output_filename = self._get_unique_individual_filename(output_folder, icon_stem)
                    else:
                        output_filename = f"{icon_stem}.png"
                    
                    output_path = os.path.join(output_folder, output_filename)
                    merged.save(output_path, 'PNG')
                    
                    # Store filename reference for index creation
                    merged.filename = output_path
                
                merged_images.append(merged)
                
                # Close source images to free memory
                icon.close()
                background.close()
                
            except Exception as e:
                print(f"Error processing {icon_path}: {e}")
                continue
        
        print(f"Successfully processed {len(merged_images)} out of {len(icon_files)} icons")
        return merged_images, folder_base_name
    
    def _get_unique_individual_filename(self, folder, base_name):
        """Get unique filename for individual files with versioning (_1, _2, etc.)"""
        counter = 0
        while True:
            if counter == 0:
                filename = f"{base_name}.png"
            else:
                filename = f"{base_name}_{counter}.png"
            
            full_path = os.path.join(folder, filename)
            if not os.path.exists(full_path):
                return filename
            counter += 1
    
    def create_spritesheet_from_images(self, images, output_path, rows, cols, 
                                     cell_size, power_of_two=False, max_pot_size=2048):
        """
        Create multiple spritesheets from list of images if needed
        
        Args:
            images (list): List of PIL.Image objects
            output_path (str): Base output path for spritesheets
            rows (int): Number of rows per sheet
            cols (int): Number of columns per sheet
            cell_size (tuple): Size of each cell
            power_of_two (bool): Whether to expand canvas to power of two
            max_pot_size (int): Maximum power of two size
            
        Returns:
            tuple: (success_status, list_of_created_files)
        """
        try:
            if not images:
                return False, []
            
            # Calculate cells per sheet
            cells_per_sheet = rows * cols
            total_images = len(images)
            
            # Calculate number of sheets needed
            num_sheets = math.ceil(total_images / cells_per_sheet)
            
            # Extract base name from output path
            output_dir = os.path.dirname(output_path)
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            
            created_files = []
            
            print(f"Creating {num_sheets} spritesheet(s) for {total_images} images...")
            
            # Create each sheet
            for sheet_num in range(num_sheets):
                # Calculate image range for this sheet
                start_idx = sheet_num * cells_per_sheet
                end_idx = min(start_idx + cells_per_sheet, total_images)
                sheet_images = images[start_idx:end_idx]
                
                # Generate sheet filename
                if num_sheets == 1:
                    sheet_filename = f"{base_name}.png"
                else:
                    sheet_filename = f"{base_name}_sheet_{sheet_num + 1}.png"
                
                sheet_path = os.path.join(output_dir, sheet_filename)
                
                print(f"Creating sheet {sheet_num + 1}/{num_sheets}: {len(sheet_images)} images -> {sheet_filename}")
                
                # Create this sheet
                success = self._create_single_spritesheet(
                    sheet_images, sheet_path, rows, cols, cell_size, power_of_two, max_pot_size
                )
                
                if success:
                    created_files.append(sheet_path)
                    print(f"✓ Sheet {sheet_num + 1} created successfully")
                else:
                    print(f"✗ Failed to create sheet {sheet_num + 1}")
                    return False, created_files
            
            print(f"All {num_sheets} spritesheet(s) created successfully!")
            return True, created_files
            
        except Exception as e:
            print(f"Error creating spritesheets: {e}")
            return False, []
    
    def _create_single_spritesheet(self, images, output_path, rows, cols, cell_size, 
                                 power_of_two=False, max_pot_size=2048):
        """
        Create a single spritesheet from images
        
        Args:
            images (list): List of PIL.Image objects (up to rows*cols)
            output_path (str): Output path for this sheet
            rows (int): Number of rows
            cols (int): Number of columns
            cell_size (tuple): Size of each cell
            power_of_two (bool): Whether to expand canvas to power of two
            max_pot_size (int): Maximum power of two size
            
        Returns:
            bool: Success status
        """
        try:
            # Calculate base sheet dimensions
            sheet_width = cols * cell_size[0]
            sheet_height = rows * cell_size[1]
            
            # Expand to power of two if requested
            if power_of_two:
                sheet_width = self._next_power_of_two(sheet_width, max_pot_size)
                sheet_height = self._next_power_of_two(sheet_height, max_pot_size)
            
            # Create spritesheet canvas
            spritesheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))
            
            # Place images in grid (only up to rows*cols images)
            max_cells = rows * cols
            images_to_place = images[:max_cells]
            
            for i, img in enumerate(images_to_place):
                row = i // cols
                col = i % cols
                
                # Calculate position
                x = col * cell_size[0]
                y = row * cell_size[1]
                
                # Resize image to cell size if needed
                if img.size != cell_size:
                    img_resized = img.resize(cell_size, Image.Resampling.LANCZOS)
                else:
                    img_resized = img
                
                # Paste image
                if img_resized.mode == 'RGBA':
                    spritesheet.paste(img_resized, (x, y), img_resized)
                else:
                    spritesheet.paste(img_resized, (x, y))
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save spritesheet
            spritesheet.save(output_path, 'PNG')
            
            # Close spritesheet to free memory
            spritesheet.close()
            
            return True
            
        except Exception as e:
            print(f"Error creating single spritesheet: {e}")
            return False
    
    def _next_power_of_two(self, value, max_value):
        """
        Get next power of two that's >= value, capped at max_value
        
        Args:
            value (int): Input value
            max_value (int): Maximum allowed value
            
        Returns:
            int: Next power of two
        """
        if value <= 1:
            return 1
        
        power = 1
        while power < value and power < max_value:
            power *= 2
        
        return min(power, max_value)
    
    # Legacy methods for backwards compatibility
    def merge_sprite_with_background(self, sprite_path, background_path, output_path):
        """Legacy method - merge single sprite with background"""
        try:
            sprite = Image.open(sprite_path).convert("RGBA")
            background = Image.open(background_path).convert("RGBA")
            
            if background.size != sprite.size:
                background = background.resize(sprite.size, Image.Resampling.LANCZOS)
            
            result = Image.alpha_composite(background, sprite)
            result.save(output_path)
            return True
            
        except Exception as e:
            print(f"Error merging images: {e}")
            return False
    
    def create_spritesheet(self, image_paths, output_path, columns=10, sprite_size=(64, 64)):
        """Legacy method - create spritesheet from file paths"""
        try:
            if not image_paths:
                return False
                
            rows = math.ceil(len(image_paths) / columns)
            sheet_width = columns * sprite_size[0]
            sheet_height = rows * sprite_size[1]
            
            spritesheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))
            
            for i, image_path in enumerate(image_paths):
                try:
                    img = Image.open(image_path).convert("RGBA")
                    img = img.resize(sprite_size, Image.Resampling.LANCZOS)
                    
                    x = (i % columns) * sprite_size[0]
                    y = (i // columns) * sprite_size[1]
                    
                    spritesheet.paste(img, (x, y), img)
                    
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
                    continue
            
            spritesheet.save(output_path)
            return True
            
        except Exception as e:
            print(f"Error creating spritesheet: {e}")
            return False
