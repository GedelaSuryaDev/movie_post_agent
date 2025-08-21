import os
import requests
import time
import re
from datetime import datetime
from typing import List, Dict
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance



# Tool 2: Movie Poster Download using OMDb API
#@tool
def download_movie_posters(movie_titles: dict) -> str:
    """
    Downloads movie posters using OMDb API for a list of movies.
    Saves posters in the 'output/photos' directory.

    Args:
        movie_titles (dict): Dictionary of movie titles with rating to download posters for movies.

    Returns:
        str: Status message with details of downloaded posters file paths.
    """
    print(f"--- Tool: download_movie_posters called ---")
    
    # Get API key from environment
    omdb_api_key = os.getenv("OMDB_API_KEY")
    if not omdb_api_key:
        return "Error: OMDB_API_KEY not found in environment variables."
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"output/photos/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse movie titles
    title_dict = movie_titles
    downloaded_posters = []
    failed_downloads = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for title, rating in title_dict.items():
        try:
            print(f"Fetching poster for: {title}")
            
            # Call OMDb API to get movie data including poster URL
            api_url = f"https://www.omdbapi.com/?t={title}&apikey={omdb_api_key}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                movie_data = response.json()
                
                # Check if the API call was successful
                if movie_data.get('Response') == 'True':
                    poster_url = movie_data.get('Poster')
                    
                    if poster_url and poster_url != 'N/A':
                        print(f"Found poster URL: {poster_url}")
                        
                        try:
                            # Download the poster image
                            poster_response = requests.get(poster_url, headers=headers, timeout=15)
                            
                            if poster_response.status_code == 200:
                                # Create safe filename
                                safe_filename = re.sub(r'[<>:"/\\|?*]', '', title)
                                safe_filename = f"{safe_filename}_{rating}"
                                file_extension = '.jpg'
                                file_path = os.path.join(output_dir, f"{safe_filename}{file_extension}")
                                
                                # Save the poster
                                with open(file_path, 'wb') as f:
                                    f.write(poster_response.content)
                                
                                downloaded_posters.append(f"{title} -> {file_path}")
                                print(f"Downloaded: {title} -> {file_path}")
                                
                            else:
                                failed_downloads.append(f"{title} (HTTP {poster_response.status_code})")
                                print(f"Failed to download poster for {title}: HTTP {poster_response.status_code}")
                                
                        except Exception as e:
                            failed_downloads.append(f"{title} (Download error)")
                            print(f"Error downloading poster for {title}: {e}")
                    else:
                        failed_downloads.append(f"{title} (No poster URL)")
                        print(f"No poster URL found for: {title}")
                else:
                    error_msg = movie_data.get('Error', 'Unknown error')
                    failed_downloads.append(f"{title} (API error: {error_msg})")
                    print(f"OMDb API error for {title}: {error_msg}")
            else:
                failed_downloads.append(f"{title} (HTTP {response.status_code})")
                print(f"Failed to call OMDb API for {title}: HTTP {response.status_code}")
            
            # Add delay between requests to be respectful
            time.sleep(1)
            
        except Exception as e:
            failed_downloads.append(f"{title} (Exception)")
            print(f"Error processing {title}: {e}")
    
    # Prepare status message
    status_message = f"Poster Download Complete!\n\n"
    status_message += f"Successfully downloaded {len(downloaded_posters)} posters:\n"
    for poster in downloaded_posters:
        status_message += f"✓ {poster}\n"
    
    if failed_downloads:
        status_message += f"\nFailed to download {len(failed_downloads)} posters:\n"
        for failed in failed_downloads:
            status_message += f"✗ {failed}\n"
    
    status_message += f"\nAll posters saved in: {os.path.abspath(output_dir)}"
    
    return status_message

# Tool 3: Image Editing
def create_final_images(raw_poster_folder: str, cover_text: str ) -> List[str]:
    """
    Processes raw posters from a folder path into final, edited images.
    It creates a cover image and saves everything to 'output/final_images'.
    Use this AFTER downloading the raw posters.

    Args:
        raw_poster_folder (str): Folder path containing the raw poster images.
        cover_text (str): Text to display on the cover collage image.

    Returns:
        List[str]: A list of file paths for the final, edited images.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    except ImportError:
        print("PIL (Pillow) not found. Install with: pip install Pillow")
        return []
    
    print(f"--- Tool: create_final_images called ---")
    save_path = f"output/final_images/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(save_path, exist_ok=True)
    final_image_paths = []
    
    # Check if folder exists
    if not os.path.exists(raw_poster_folder):
        print(f"Error: Folder {raw_poster_folder} does not exist")
        return final_image_paths
    
    # Get all .jpg image files from the folder
    raw_poster_paths = []
    
    for filename in os.listdir(raw_poster_folder):
        if filename.lower().endswith('.jpg'):
            full_path = os.path.join(raw_poster_folder, filename)
            raw_poster_paths.append(full_path)
    
    if not raw_poster_paths:
        print(f"No image files found in {raw_poster_folder}")
        return final_image_paths
    
    print(f"Found {len(raw_poster_paths)} image files in {raw_poster_folder}")
    
    # Create cover image (collage of first 4 posters)
    cover_path = os.path.join(save_path, "00_cover_collage.jpg")
    try:
        cover_image = create_movie_collage(raw_poster_paths[:4], cover_text )
        cover_image.save(cover_path, "JPEG", quality=95)
        final_image_paths.append(cover_path)
        print(f"Created cover collage: {cover_path}")
    except Exception as e:
        print(f"Error creating cover: {e}")
    
    # Process individual posters with enhancements
    for i, path in enumerate(raw_poster_paths):
        try:
            # Load and enhance image
            with Image.open(path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to standard dimensions (300x450)
                img = img.resize((300, 450), Image.Resampling.LANCZOS)
                
                # Enhance image quality
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)
                
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.1)
                
                # Add border, ranking number, and IMDb rating
                # Extract movie title from path for rating lookup
                movie_title = os.path.splitext(os.path.basename(path))[0]
                img_with_border = add_movie_border_and_ranking(img, i + 1, movie_title)
                
                # Save enhanced image
                safe_filename = re.sub(r'[<>:"/\\|?*]', '', os.path.splitext(os.path.basename(path))[0])
                final_path = os.path.join(save_path, f"{i+1:02d}_{safe_filename}_enhanced.jpg")
                img_with_border.save(final_path, "JPEG", quality=95)
                final_image_paths.append(final_path)
                print(f"Enhanced poster {i+1}: {final_path}")
                
        except Exception as e:
            print(f"Error processing {path}: {e}")
            # Fallback: copy original
            try:
                safe_filename = re.sub(r'[<>:"/\\|?*]', '', os.path.splitext(os.path.basename(path))[0])
                final_path = os.path.join(save_path, f"{i+1:02d}_{safe_filename}.jpg")
                shutil.copy(path, final_path)
                final_image_paths.append(final_path)
            except Exception as copy_error:
                print(f"Error copying {path}: {copy_error}")
    
    return final_image_paths

def create_movie_collage(poster_paths: List[str], cover_text: str) -> Image.Image:
    """Creates a 2x2 collage from up to 4 movie posters."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create canvas
    canvas_size = (600, 900)  # 2x2 grid of 300x450 posters
    canvas = Image.new('RGB', canvas_size, (20, 20, 20))
    
    # Load and resize posters
    posters = []
    for path in poster_paths[:4]:
        try:
            with Image.open(path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img = img.resize((300, 450), Image.Resampling.LANCZOS)
                posters.append(img.copy())
        except Exception as e:
            print(f"Error loading poster {path}: {e}")
    
    # Arrange in 2x2 grid
    positions = [(0, 0), (300, 0), (0, 450), (300, 450)]
    for i, poster in enumerate(posters):
        if i < len(positions):
            canvas.paste(poster, positions[i])
    
    # Add title overlay
    draw = ImageDraw.Draw(canvas)
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Add semi-transparent overlay for text
    overlay = Image.new('RGBA', canvas_size, (0, 0, 0, 128))
    canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay).convert('RGB')
    
    # Add text
    draw = ImageDraw.Draw(canvas)
    text = cover_text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (canvas_size[0] - text_width) // 2
    y = canvas_size[1] - 60
    
    # Text with outline
    for adj in range(-2, 3):
        for adj2 in range(-2, 3):
            draw.text((x + adj, y + adj2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    return canvas

def add_movie_border_and_ranking(img: Image.Image, rank: int, movie_title: str = "") -> Image.Image:
    """Adds a border, ranking number, and IMDb rating to a movie poster."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create new image with border
    border_size = 10
    new_size = (img.width + 2 * border_size, img.height + 2 * border_size)
    bordered_img = Image.new('RGB', new_size, (255, 215, 0))  # Gold border
    bordered_img.paste(img, (border_size, border_size))
    
    draw = ImageDraw.Draw(bordered_img)
    
    # Get fonts
    try:
        rank_font = ImageFont.truetype("arial.ttf", 24)
        rating_font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 16)
        imdb_font = ImageFont.truetype("arial.ttf", 12)
    except:
        rank_font = ImageFont.load_default()
        rating_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        imdb_font = ImageFont.load_default()
    
    # Create circular badge for ranking (top-left)
    badge_size = 40
    badge_center = (border_size + badge_size // 2, border_size + badge_size // 2)
    
    # Draw ranking badge background
    draw.ellipse([
        badge_center[0] - badge_size // 2,
        badge_center[1] - badge_size // 2,
        badge_center[0] + badge_size // 2,
        badge_center[1] + badge_size // 2
    ], fill=(220, 20, 60), outline=(255, 255, 255), width=3)
    
    # Add ranking number
    rank_text = str(rank)
    bbox = draw.textbbox((0, 0), rank_text, font=rank_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = badge_center[0] - text_width // 2
    text_y = badge_center[1] - text_height // 2
    draw.text((text_x, text_y), rank_text, font=rank_font, fill=(255, 255, 255))
    
    # Get IMDb rating for the movie from filename
    imdb_rating = extract_rating_from_filename(movie_title)
    
    # Always create IMDb badge - use default rating if not found
    if not imdb_rating:
        imdb_rating = "8.0"  # Default rating for testing
    
        # Create IMDb rating badge (top-right)
    rating_badge_width = 90
    rating_badge_height = 35
    rating_x = bordered_img.width - border_size - rating_badge_width - 5
    rating_y = border_size + 5
        
    # Draw rating badge background with stronger colors
    draw.rounded_rectangle([
            rating_x, rating_y,
            rating_x + rating_badge_width, rating_y + rating_badge_height
    ], radius=8, fill=(245, 197, 24), outline=(0, 0, 0), width=3)  # IMDb yellow with black border
        
    # Add IMDb logo text at top of badge
    imdb_text = "IMDb"
    bbox = draw.textbbox((0, 0), imdb_text, font=imdb_font)
    imdb_width = bbox[2] - bbox[0]
    imdb_x = rating_x + (rating_badge_width - imdb_width) // 2
    imdb_y = rating_y + 3
    # Add text shadow for better visibility
    draw.text((imdb_x + 1, imdb_y + 1), imdb_text, font=imdb_font, fill=(255, 255, 255))
    draw.text((imdb_x, imdb_y), imdb_text, font=imdb_font, fill=(0, 0, 0))
        
    # Add rating with star symbol at bottom of badge
    rating_text = f"★ {imdb_rating}"
    bbox = draw.textbbox((0, 0), rating_text, font=small_font)
    rating_width = bbox[2] - bbox[0]
    rating_text_x = rating_x + (rating_badge_width - rating_width) // 2
    rating_text_y = rating_y + 18
    # Add text shadow for better visibility
    draw.text((rating_text_x + 1, rating_text_y + 1), rating_text, font=small_font, fill=(255, 255, 255))
    draw.text((rating_text_x, rating_text_y), rating_text, font=small_font, fill=(0, 0, 0))
    
    # Add movie title at bottom with semi-transparent background
    if movie_title:
        # Clean up title for display
        display_title = movie_title.replace('_', ' ').title()
        if len(display_title) > 25:
            display_title = display_title[:22] + "..."
        
        # Create semi-transparent overlay for title
        title_height = 40
        title_y = bordered_img.height - title_height
        # Create full-size overlay with transparency only at bottom
        full_overlay = Image.new('RGBA', bordered_img.size, (0, 0, 0, 0))
        title_overlay = Image.new('RGBA', (bordered_img.width, title_height), (0, 0, 0, 180))
        full_overlay.paste(title_overlay, (0, title_y))
        
        bordered_img = Image.alpha_composite(bordered_img.convert('RGBA'), full_overlay).convert('RGB')
        
        # Add title text
        draw = ImageDraw.Draw(bordered_img)
        bbox = draw.textbbox((0, 0), display_title, font=rating_font)
        title_width = bbox[2] - bbox[0]
        title_x = (bordered_img.width - title_width) // 2
        title_text_y = title_y + 10
        
        # Text with outline for better visibility
        for adj in range(-1, 2):
            for adj2 in range(-1, 2):
                draw.text((title_x + adj, title_text_y + adj2), display_title, font=rating_font, fill=(0, 0, 0))
        draw.text((title_x, title_text_y), display_title, font=rating_font, fill=(255, 255, 255))
    
    return bordered_img

def extract_rating_from_filename(filename: str) -> str:
    """Extracts IMDb rating from filename format: 'MovieTitle_8.5.jpg'"""
    if not filename:
        return ""
    
    # Remove file extension if present
    name_without_ext = os.path.splitext(filename)[0]
    
    # Look for rating pattern at the end: _X.X format
    import re
    rating_pattern = r'_(\d+\.\d+)$'
    match = re.search(rating_pattern, name_without_ext)
    
    if match:
        return match.group(1)
    
    return ""

