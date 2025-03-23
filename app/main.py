from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import os
import asyncio
import uvicorn
from pathlib import Path
import logging

# Import our custom modules
from app.data_loader import DataLoader
from app.rag import RAGSystem
from app.agents import AgentSystem
from app.visualization import Visualizer
from app.image_generator import ImageGenerator
from app.visualization_3d import Biosphere3DVisualizer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the app
app = FastAPI(title="BioSphere 2 Explorer API")

# Configure CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static files directory for images and 3D models
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
(static_dir / "models").mkdir(exist_ok=True)  # Ensure models directory exists
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize components
data_loader = DataLoader(data_dir="data/raw")
agent_system = AgentSystem(data_loader)
visualizer = Visualizer(data_loader)
image_generator = ImageGenerator(image_dir="static/images")
biosphere_3d = Biosphere3DVisualizer(model_dir="static/models", data_dir="data/raw")

# Define request and response models
class ChatRequest(BaseModel):
    message: str
    agent: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    suggested_visualizations: List[Dict[str, Any]]

class VisualizationRequest(BaseModel):
    type: str
    location: str
    variable: str
    title: Optional[str] = None
    
class ComparisonRequest(BaseModel):
    locations: List[str]
    variable: str
    title: Optional[str] = None
    
class ImageRequest(BaseModel):
    location: str
    feature: Optional[str] = None

class EnvironmentUpdateRequest(BaseModel):
    location: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[float] = None
    light: Optional[float] = None

# Define API endpoints
@app.get("/")
async def read_root():
    return {"message": "Welcome to BioSphere 2 Explorer API"}

@app.get("/api/locations")
async def get_locations():
    return {"locations": data_loader.get_locations()}

@app.get("/api/variables/{location}")
async def get_variables(location: str):
    variables = data_loader.get_variables(location)
    if not variables:
        raise HTTPException(status_code=404, detail=f"Location '{location}' not found")
    return {"variables": variables}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return a response"""
    # Get response from agent system
    agent_name = request.agent
    response = agent_system.route_query(request.message, agent_name)
    
    # If agent_name wasn't provided, try to determine it from the response
    if not agent_name:
        for location in data_loader.get_locations():
            if location in response[:100]:  # Check the beginning of the response
                agent_name = location
                break
        
        # Default to general if still not determined
        if not agent_name:
            agent_name = "General"
    
    # Get visualization suggestions
    suggestions = visualizer.suggest_visualizations(request.message, agent_name)
    
    return {
        "response": response,
        "agent_used": agent_name,
        "suggested_visualizations": suggestions
    }

@app.post("/api/visualize/time_series")
async def create_time_series(request: VisualizationRequest):
    """Create a time series visualization"""
    viz_data = visualizer.create_time_series(
        location=request.location,
        variable=request.variable,
        title=request.title,
        format='plotly_json'
    )
    
    if not viz_data:
        raise HTTPException(status_code=404, detail="Could not create visualization with provided parameters")
        
    return {"visualization": viz_data}

@app.post("/api/visualize/distribution")
async def create_distribution(request: VisualizationRequest):
    """Create a distribution visualization"""
    viz_data = visualizer.create_distribution(
        location=request.location,
        variable=request.variable,
        title=request.title,
        format='plotly_json'
    )
    
    if not viz_data:
        raise HTTPException(status_code=404, detail="Could not create visualization with provided parameters")
        
    return {"visualization": viz_data}

@app.post("/api/visualize/comparison")
async def create_comparison(request: ComparisonRequest):
    """Create a comparison visualization across locations"""
    viz_data = visualizer.create_comparison(
        locations=request.locations,
        variable=request.variable,
        title=request.title,
        format='plotly_json'
    )
    
    if not viz_data:
        raise HTTPException(status_code=404, detail="Could not create visualization with provided parameters")
        
    return {"visualization": viz_data}

@app.post("/api/generate_image")
async def generate_environment_image(request: ImageRequest):
    """Generate an image of a specific environment"""
    try:
        image_data = await image_generator.get_environment_image(
            location=request.location,
            feature=request.feature
        )
        
        if not image_data:
            raise HTTPException(status_code=500, detail="Image generation failed")
            
        return {"image": image_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

@app.get("/api/3d/state/{location}")
async def get_3d_state(location: str):
    """Get initial 3D visualization state for a location"""
    logger.debug(f"Getting initial 3D state for location: {location}")
    state = biosphere_3d.get_initial_state(location)
    if not state:
        logger.error(f"Failed to get 3D state for location: {location}")
        raise HTTPException(status_code=404, detail=f"3D model not found for location '{location}'")
    logger.debug(f"Returning 3D state: {state}")
    return state

@app.post("/api/3d/update")
async def update_3d_environment(request: EnvironmentUpdateRequest):
    """Update environment parameters for 3D visualization"""
    logger.debug(f"Updating 3D environment for location: {request.location}")
    # Filter out None values
    params = {k: v for k, v in request.dict().items() if k != 'location' and v is not None}
    
    if not params:
        logger.error("No parameters provided for update")
        raise HTTPException(status_code=400, detail="No parameters provided for update")
        
    state = biosphere_3d.update_environment(params, request.location)
    if not state:
        logger.error(f"Failed to update environment for location: {request.location}")
        raise HTTPException(status_code=404, detail=f"3D model not found for location '{request.location}'")
        
    logger.debug(f"Returning updated state: {state}")
    return state

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)