# BioSphereAI - Team Ryukendo (#46)

This project implements a BioSphere 2 Explorer that integrates environmental data analysis, AI-powered conversational agents (RAG), dynamic visualization tools (2D/3D), and automated image generation to enable interactive exploration and real-time simulation of ecological systems through a unified interface.

![Image](https://github.com/AI-Core-Biosphere-2/BioSphereAI/blob/main/static/images/Ocean_biome_in_BioSphere_2_0_1021.jpg?raw=true)

## Table of Contents

- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Description

This project is a Streamlit & FastAPI-based AI powered system for the "BioSphere 2 Explorer," an interactive platform that seamlessly integrates environmental data analysis, AI agents, and advanced visualization tools to explore ecological systems.

## Components

1. **DataLoader**: Manages and handles environmental datasets.
2. **AgentSystem**: Includes AI agents that adeptly process natural language queries.
3. **Visualizer**: Creates detailed time-series plots and comparisons.
4. **ImageGenerator**: Produces environment imagery.
5. **Biosphere3DVisualizer**: Generates interactive 3D models of biosphere locations.

![Image](https://github.com/AI-Core-Biosphere-2/BioSphereAI/blob/main/static/models/Architecture_diagram.jpg?raw=true)

## Key Features

- **Chat-based Interaction**: Provides auto-suggested visualizations based on user queries.
- **Dynamic 3D Environment Updates**: Allows adjustments to environment parameters like `temperature, Humidity, Light and CO₂` levels.
- **Multi-User Collaboration & Cloud Hosting**: Developed multi agent network so that where multiple users/LLM Agents can interact in real time and work together to generate insights.

- **Data Exploration and Visualization**: Offers comprehensive endpoints for accessing and visually representing location and variable data.

## Installation

### Prerequisites

- To run this project we need `Blender` (headless) to interact with 3D model and other python packeages mentioned in `reqirement.txt` and `streamlit_requirements.txt`

### Steps

1. Clone the repository:
   ```sh
   git clone https://github.com/AI-Core-Biosphere-2/BioSphereAI
   ```
2. Navigate to the project directory:

   ```sh
   cd BioSphereAI
   ```

3. Create Python virtual environment:

   ```sh
   python -m venv myenv
   ```

4. Activate virtual env:

   ```sh
   source ./myenv/bin/activate
   ```

5. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

6. Install streamlit dependencies:

   ```sh
   pip install -r streamlit_requirements.txt
   ```

7. Install Blener:

   ###### Linux (ubuntu)

   ```sh
   sudo apt update && sudo apt upgrade -y
   sudo apt install blender -y
   ```

   ###### MacOS

   ```sh
   brew install --cask blender
   ```

8. Set Huggingface token:
   ###### Linux (ubuntu) / MacOS
   ```sh
   echo "HUGGINGFACE_API_KEY=your_actual_huggingface_api_key" > .env
   ```

## Usage

1. Run backend:

   ```sh
   uvicorn app.main:app --port 8000
   ```

2. Run frontend:
   ```sh
   streamlit run streamlit_app/app.py
   ```

## Future Plans

- **AI Model Enhancements**: Improve AI agent capabilities for more accurate and context-aware interactions.
- **Expanded Dataset Integration**: Support additional environmental datasets for broader simulation capabilities.
- **Advanced 3D Visualizations**: Introduce more detailed and realistic rendering for ecological simulations.
- **Real-time Environmental Simulation**: Enable predictive modeling and dynamic environment adjustments.
- **User Customization Features**: Allow users to modify simulation parameters and explore personalized scenarios.
- **Integration with IoT Sensors**: Connect with real-world biosphere sensors for live 3D data visualization.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project is part of **HackAZ** - BioSphere 2 **B2Twin-Hackathon**
