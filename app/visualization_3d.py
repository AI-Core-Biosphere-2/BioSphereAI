import json
from pathlib import Path
import os
from typing import Dict, Any, Optional, List
import subprocess
import shutil
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Biosphere3DVisualizer:
    def __init__(self, model_dir: str = "static/models", data_dir: str = "data"):
        self.model_dir = Path(model_dir)
        self.data_dir = Path(data_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.base_model_path = self.data_dir / "Biosphere+Truss+Landscape.blend"
        logger.debug(f"Looking for Blender file at: {self.base_model_path}")
        if self.base_model_path.exists():
            logger.debug("Found Blender file")
        else:
            logger.error(f"Blender file not found at {self.base_model_path}")
        
        self.environment_params = {
            'temperature': 25.0,  # Celsius
            'humidity': 60.0,     # Percentage
            'co2': 400.0,        # ppm
            'light': 100.0       # Percentage
        }
        
        # Biome-specific parameters
        self.biome_params = {
            'Desert': {
                'base_temp': 30.0,
                'base_humidity': 30.0,
                'color_tint': [1.0, 0.8, 0.6],  # Sandy colors
                'light_intensity': 1.2,
                'fog_density': 0.1
            },
            'Rainforest': {
                'base_temp': 28.0,
                'base_humidity': 85.0,
                'color_tint': [0.6, 0.8, 0.6],  # Green tint
                'light_intensity': 0.8,
                'fog_density': 0.3
            },
            'Ocean': {
                'base_temp': 25.0,
                'base_humidity': 90.0,
                'color_tint': [0.6, 0.7, 0.9],  # Blue tint
                'light_intensity': 0.9,
                'fog_density': 0.4
            },
            'LEO-W': {
                'base_temp': 22.0,
                'base_humidity': 70.0,
                'color_tint': [0.8, 0.8, 0.8],  # Neutral
                'light_intensity': 1.0,
                'fog_density': 0.2
            }
        }
        
    def _convert_blend_to_gltf(self, blend_path: Path, gltf_path: Path) -> bool:
        """Convert Blender file to glTF format using Blender's command line interface"""
        try:
            logger.debug(f"Starting conversion from {blend_path} to {gltf_path}")
            
            # Convert paths to forward slashes for Blender script
            blend_path_str = str(blend_path).replace('\\', '/')
            gltf_path_str = str(gltf_path).replace('\\', '/')
            
            # Create a temporary Python script for Blender
            script_content = f"""
import bpy
import os

print(f"Current working directory: {{os.getcwd()}}")
print(f"Attempting to open: {blend_path_str}") 

bpy.ops.wm.open_mainfile(filepath='{blend_path_str}')
print("File loaded successfully")

print("Starting glTF export...")
bpy.ops.export_scene.gltf(
    filepath='{gltf_path_str}',
    export_format='GLB',
    export_draco_mesh_compression_enable=True
)
print("Export completed")
"""
            script_path = self.model_dir / "convert_script.py"
            with open(script_path, "w") as f:
                f.write(script_content)
            
            logger.debug("Running Blender conversion...")
            # Run Blender in background mode to convert the file
            result = subprocess.run([
                "blender",
                "--background",
                "--python", str(script_path)
            ], check=True, capture_output=True, text=True)
            
            logger.debug(f"Blender stdout: {result.stdout}")
            logger.debug(f"Blender stderr: {result.stderr}")
            
            # Clean up temporary script
            script_path.unlink()
            
            if gltf_path.exists():
                logger.debug(f"Conversion successful, glTF file created at {gltf_path}")
                return True
            else:
                logger.error("Conversion completed but glTF file not found")
                return False
            
        except Exception as e:
            logger.error(f"Error converting Blender file: {e}")
            return False
        
    def load_model(self, location: str) -> bool:
        """Load the 3D model for a specific location"""
        logger.debug(f"Loading model for location: {location}")
        
        # Use the base model path
        gltf_path = self.model_dir / "biosphere_base.glb"
        logger.debug(f"Looking for glTF file at: {gltf_path}")
        
        # If glTF doesn't exist, convert from the base Blender file
        if not gltf_path.exists():
            logger.debug("glTF file not found, attempting conversion")
            if not self.base_model_path.exists():
                logger.error(f"Base model not found at {self.base_model_path}")
                return False
                
            logger.debug(f"Converting {self.base_model_path} to {gltf_path}")
            if not self._convert_blend_to_gltf(self.base_model_path, gltf_path):
                return False
            
        try:
            # Instead of loading with PyVista, we'll just verify the file exists
            if not gltf_path.exists():
                logger.error("glTF file still not found after conversion attempt")
                return False
                
            # Get the relative path for serving through FastAPI static files
            self.model_url = f"/models/biosphere_base.glb"
            logger.debug(f"Model URL set to: {self.model_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error preparing model: {e}")
            return False
            
    def update_environment(self, params: Dict[str, float], location: str) -> Dict[str, Any]:
        """Update environment parameters and return visualization data"""
        # First ensure the model is loaded
        if not self.load_model(location):
            return None
            
        # Update parameters
        self.environment_params.update(params)
        
        # Get biome-specific parameters
        biome = self.biome_params.get(location, self.biome_params['LEO-W'])
        
        # Create visualization data
        viz_data = {
            'model_url': self.model_url,
            'environment': self.environment_params,
            'effects': self._calculate_environmental_effects(biome)
        }
        
        return viz_data
        
    def _calculate_environmental_effects(self, biome: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate visual effects based on environment parameters and biome"""
        temp = self.environment_params['temperature']
        humidity = self.environment_params['humidity']
        co2 = self.environment_params['co2']
        light = self.environment_params['light']
        
        # Calculate variations from biome baseline with more pronounced effects
        temp_factor = (temp - biome['base_temp']) / 20  # More sensitive to temperature changes
        humidity_factor = (humidity - biome['base_humidity']) / 50  # More sensitive to humidity
        co2_factor = (co2 - 400) / 600  # Normalize CO2 effect
        light_factor = light / 100
        
        # Combine biome-specific effects with environmental parameters
        base_color = biome['color_tint']
        
        # Temperature affects the redness/warmth
        temp_color = [
            min(1.0, base_color[0] * (1.0 + temp_factor * 0.5)),  # More red when hot
            base_color[1] * (1.0 - abs(temp_factor) * 0.3),  # Reduce green with extreme temps
            base_color[2] * (1.0 - temp_factor * 0.3)  # Less blue when hot
        ]
        
        # CO2 affects the color saturation and fog
        atmosphere_color = [
            temp_color[0] * (0.8 + co2_factor * 0.4),
            temp_color[1] * (0.8 + co2_factor * 0.2),
            temp_color[2] * (0.8 - co2_factor * 0.2)  # Higher CO2 reduces blue
        ]
        
        return {
            'color_intensity': biome['light_intensity'] * (1.0 + (temp_factor * 0.3)),
            'opacity': max(0.1, min(1.0, biome['fog_density'] + humidity_factor * 0.5)),  # More pronounced fog with humidity
            'atmosphere_color': atmosphere_color,
            'light_intensity': biome['light_intensity'] * light_factor * (1.0 - co2_factor * 0.2),  # CO2 slightly reduces light
            'biome_tint': biome['color_tint']
        }
        
    def get_initial_state(self, location: str) -> Dict[str, Any]:
        """Get initial visualization state for a location"""
        if not self.load_model(location):
            return None
            
        # Get biome-specific parameters
        biome = self.biome_params.get(location, self.biome_params['LEO-W'])
        
        return {
            'model_url': self.model_url,
            'environment': self.environment_params,
            'effects': self._calculate_environmental_effects(biome)
        } 