import os
import requests
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import base64
from PIL import Image
import io
import random

# Load environment variables
load_dotenv()
API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not API_KEY:
    print("Warning: Huggingface API Key is missing in the environment file.")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {API_KEY}"}

class ImageGenerator:
    def __init__(self, image_dir="static/images"):
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
    async def query_model(self, payload):
        """Send query to Hugging Face API"""
        try:
            response = await asyncio.to_thread(
                requests.post, 
                API_URL, 
                headers=headers, 
                json=payload
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
            
    async def generate_image(self, prompt, num_images=1):
        """Generate images based on prompt"""
        prompts = []
        
        # Enhance prompt for better environmental visualizations
        base_prompt = f"A photorealistic visualization of {prompt} in BioSphere 2, highly detailed scientific visualization"
        
        for i in range(num_images):
            # Add randomness for variety
            seed = random.randint(0, 1000000)
            prompts.append({
                "inputs": f"{base_prompt}, quality=4k, sharp details, scientific accuracy, seed={seed}"
            })
            
        # Generate images in parallel
        tasks = [self.query_model(p) for p in prompts]
        image_contents = await asyncio.gather(*tasks)
        
        # Save images and collect URLs
        image_urls = []
        
        for i, img_content in enumerate(image_contents):
            if img_content:
                # Create clean filename
                clean_prompt = prompt.replace(" ", "_").replace(",", "").replace(".", "")
                file_path = self.image_dir / f"{clean_prompt}_{i}_{random.randint(1000, 9999)}.jpg"
                
                # Save image
                with open(file_path, "wb") as f:
                    f.write(img_content)
                    
                # Add to URLs
                image_urls.append(str(file_path))
                
        return image_urls
        
    def encode_image_to_base64(self, image_path):
        """Convert image to base64 for embedding in HTML"""
        try:
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()
                return f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None
            
    async def get_environment_image(self, location, feature=None):
        """Generate an image of a specific environment location"""
        if not API_KEY:
            return None
            
        prompt = f"{location} biome in BioSphere 2"
        
        if feature:
            prompt += f", focusing on {feature}"
            
        # Check if we have cached images
        clean_prompt = prompt.replace(" ", "_").replace(",", "").replace(".", "")
        existing_images = list(self.image_dir.glob(f"{clean_prompt}_*.jpg"))
        
        # Return cached image if available
        if existing_images:
            return self.encode_image_to_base64(random.choice(existing_images))
            
        # Otherwise generate new image
        image_urls = await self.generate_image(prompt, num_images=1)
        
        if image_urls:
            return self.encode_image_to_base64(image_urls[0])
            
        return None