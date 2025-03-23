import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import plotly.graph_objects as go
import pandas as pd
from PIL import Image
import base64
import io
import os

# API endpoints
API_URL = "http://localhost:8000"
STATIC_URL = f"{API_URL}/static"  # Add static URL

# Set page config
st.set_page_config(
    page_title="BioSphere 2 Explorer",
    page_icon="🌍",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = None
    
if 'current_suggestions' not in st.session_state:
    st.session_state.current_suggestions = []
    
if 'locations' not in st.session_state:
    # Get locations from API
    try:
        response = requests.get(f"{API_URL}/api/locations")
        if response.status_code == 200:
            st.session_state.locations = response.json()['locations']
        else:
            st.session_state.locations = []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        st.session_state.locations = ["Desert", "Rainforest", "Ocean", "LEO-W"]

# Title and description
st.title("BioSphere 2 Data Explorer")
st.markdown("Explore environmental data from different biomes in BioSphere 2")

# Create two columns for layout
col1, col2 = st.columns([1, 1])

# Left column - Chat interface
with col1:
    st.header("Chat with BioSphere 2 Assistant")
    
    # Agent selection
    agent = st.selectbox(
        "Select a biome to focus on:",
        ["Auto-detect"] + st.session_state.locations
    )
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Assistant:** {message['content']}")
                
    # User input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area("Your message:", height=100)
        submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input:
            # Add user message to history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Prepare request data
            request_data = {
                'message': user_input,
                'agent': None if agent == "Auto-detect" else agent
            }
            
            try:
                # Make API request
                response = requests.post(
                    f"{API_URL}/api/chat",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': result['response']
                    })
                    
                    # Store current agent and suggestions
                    st.session_state.current_agent = result['agent_used']
                    st.session_state.current_suggestions = result['suggested_visualizations']
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error connecting to API: {e}")
                
            # Rerun to update
            st.rerun()

# Right column - Visualizations
with col2:
    st.header("Data Visualizations")
    
    # 3D Visualization Section
    if st.session_state.current_agent and st.session_state.current_agent != "General":
        st.subheader("3D Environment Simulation")
        
        # Create a container for the 3D viewer
        viewer_container = st.container()
        
        # Environment controls
        with st.expander("Environment Controls", expanded=True):
            col_temp, col_humidity = st.columns(2)
            
            with col_temp:
                temperature = st.slider(
                    "Temperature (°C)",
                    min_value=15.0,
                    max_value=35.0,
                    value=25.0,
                    step=0.5
                )
                
            with col_humidity:
                humidity = st.slider(
                    "Humidity (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=60.0,
                    step=1.0
                )
                
            col_co2, col_light = st.columns(2)
            
            with col_co2:
                co2 = st.slider(
                    "CO₂ (ppm)",
                    min_value=300.0,
                    max_value=1000.0,
                    value=400.0,
                    step=10.0
                )
                
            with col_light:
                light = st.slider(
                    "Light (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=100.0,
                    step=1.0
                )
        
        # Update environment parameters
        try:
            response = requests.post(
                f"{API_URL}/api/3d/update",
                json={
                    'location': st.session_state.current_agent,
                    'temperature': temperature,
                    'humidity': humidity,
                    'co2': co2,
                    'light': light
                }
            )
            
            if response.status_code == 200:
                viz_data = response.json()
                
                # Create Three.js visualization using components
                with viewer_container:
                    components.html(
                        f"""
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
                        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
                        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
                        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/DRACOLoader.js"></script>
                        
                        <div id="threejs-container" style="width: 100%; height: 400px; background: #000; border-radius: 10px; overflow: hidden;"></div>
                        
                        <script>
                            // Wait for Three.js to load
                            window.addEventListener('load', function() {{
                                console.log('Initializing Three.js viewer...');
                                
                                // Initialize Three.js scene
                                const scene = new THREE.Scene();
                                const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
                                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                                const container = document.getElementById('threejs-container');
                                
                                renderer.setSize(container.offsetWidth, 400);
                                renderer.setClearColor(0x000000, 1);
                                container.appendChild(renderer.domElement);
                                
                                console.log('Scene initialized');
                                
                                // Add controls
                                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                                controls.enableDamping = true;
                                controls.dampingFactor = 0.05;
                                controls.screenSpacePanning = true;
                                controls.minDistance = 2;
                                controls.maxDistance = 100;
                                controls.maxPolarAngle = Math.PI;  // Allow full vertical rotation
                                
                                // Add ambient light for base illumination
                                const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
                                scene.add(ambientLight);
                                
                                // Set up DRACO loader
                                const dracoLoader = new THREE.DRACOLoader();
                                dracoLoader.setDecoderPath('https://www.gstatic.com/draco/v1/decoders/');
                                
                                // Set up GLTF loader
                                const loader = new THREE.GLTFLoader();
                                loader.setDRACOLoader(dracoLoader);
                                
                                const modelUrl = '{STATIC_URL}' + '{viz_data["model_url"]}';
                                console.log('Loading model from:', modelUrl);
                                
                                // Load model
                                loader.load(modelUrl, 
                                    function(gltf) {{
                                        console.log('Model loaded successfully');
                                        const model = gltf.scene;
                                        
                                        // Apply environmental effects
                                        const effects = {json.dumps(viz_data["effects"])};
                                        
                                        // Add directional lights from multiple angles
                                        const lights = [
                                            {{ position: [1, 1, 1], intensity: effects.light_intensity }},
                                            {{ position: [-1, 1, -1], intensity: effects.light_intensity * 0.5 }},
                                            {{ position: [0, -1, 0], intensity: effects.light_intensity * 0.3 }}
                                        ];
                                        
                                        lights.forEach(light => {{
                                            const directionalLight = new THREE.DirectionalLight(
                                                new THREE.Color(...effects.atmosphere_color),
                                                light.intensity
                                            );
                                            directionalLight.position.set(...light.position);
                                            scene.add(directionalLight);
                                        }});
                                        
                                        // Add fog with adjusted density
                                        scene.fog = new THREE.FogExp2(
                                            new THREE.Color(...effects.atmosphere_color).getHex(),
                                            effects.opacity * 0.02  // Reduced fog density
                                        );
                                        
                                        // Add model to scene
                                        scene.add(model);
                                        
                                        // Center and position camera
                                        const box = new THREE.Box3().setFromObject(model);
                                        const center = box.getCenter(new THREE.Vector3());
                                        const size = box.getSize(new THREE.Vector3());
                                        const maxDim = Math.max(size.x, size.y, size.z);
                                        
                                        // Position camera at an angle
                                        camera.position.set(
                                            center.x + maxDim * 1.5,
                                            center.y + maxDim * 1.0,
                                            center.z + maxDim * 1.5
                                        );
                                        camera.lookAt(center);
                                        
                                        // Update controls target
                                        controls.target.copy(center);
                                        controls.update();
                                        
                                        console.log('Scene setup complete');
                                    }},
                                    function(xhr) {{
                                        console.log('Loading progress:', (xhr.loaded / xhr.total * 100) + '% loaded');
                                    }},
                                    function(error) {{
                                        console.error('Error loading model:', error);
                                    }}
                                );
                                
                                // Animation loop
                                function animate() {{
                                    requestAnimationFrame(animate);
                                    controls.update();
                                    renderer.render(scene, camera);
                                }}
                                animate();
                                
                                // Handle window resize
                                function onWindowResize() {{
                                    const container = document.getElementById('threejs-container');
                                    camera.aspect = container.offsetWidth / 400;
                                    camera.updateProjectionMatrix();
                                    renderer.setSize(container.offsetWidth, 400);
                                }}
                                
                                window.addEventListener('resize', onWindowResize, false);
                            }});
                        </script>
                        """,
                        height=400
                    )
        except Exception as e:
            st.error(f"Error updating 3D visualization: {e}")
    
    # Visualization suggestions
    if 'current_suggestions' in st.session_state and st.session_state.current_suggestions:
        st.subheader("Suggested Visualizations")
        
        for i, suggestion in enumerate(st.session_state.current_suggestions):
            with st.expander(suggestion['title'], expanded=i==0):
                st.write(suggestion['description'])
                
                if suggestion['type'] == 'time_series':
                    if st.button(f"Generate Time Series", key=f"viz_{i}"):
                        try:
                            response = requests.post(
                                f"{API_URL}/api/visualize/time_series",
                                json={
                                    'type': 'time_series',
                                    'location': suggestion['location'],
                                    'variable': suggestion['variable'],
                                    'title': suggestion['title']
                                }
                            )
                            
                            if response.status_code == 200:
                                viz_data = response.json()['visualization']
                                fig = go.Figure(viz_data)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.error(f"Error generating visualization: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                elif suggestion['type'] == 'distribution':
                    if st.button(f"Generate Distribution", key=f"viz_{i}"):
                        try:
                            response = requests.post(
                                f"{API_URL}/api/visualize/distribution",
                                json={
                                    'type': 'distribution',
                                    'location': suggestion['location'],
                                    'variable': suggestion['variable'],
                                    'title': suggestion['title']
                                }
                            )
                            
                            if response.status_code == 200:
                                viz_data = response.json()['visualization']
                                fig = go.Figure(viz_data)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.error(f"Error generating visualization: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                elif suggestion['type'] == 'comparison':
                    if st.button(f"Generate Comparison", key=f"viz_{i}"):
                        try:
                            response = requests.post(
                                f"{API_URL}/api/visualize/comparison",
                                json={
                                    'locations': suggestion['locations'],
                                    'variable': suggestion['variable'],
                                    'title': suggestion['title']
                                }
                            )
                            
                            if response.status_code == 200:
                                viz_data = response.json()['visualization']
                                fig = go.Figure(viz_data)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.error(f"Error generating visualization: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    # Custom visualization section
    st.subheader("Custom Visualization")
    with st.form(key="custom_viz_form"):
        viz_type = st.selectbox(
            "Visualization Type",
            ["Time Series", "Distribution", "Comparison"]
        )
        
        if viz_type == "Comparison":
            # Multi-select for locations
            locations = st.multiselect(
                "Select Locations",
                st.session_state.locations,
                default=[st.session_state.locations[0]]
            )
            
            # Get common variables across selected locations
            common_variables = []
            if locations:
                try:
                    all_variables = []
                    for location in locations:
                        response = requests.get(f"{API_URL}/api/variables/{location}")
                        if response.status_code == 200:
                            all_variables.append(set(response.json()['variables']))
                    
                    if all_variables:
                        common_variables = list(set.intersection(*all_variables))
                except Exception as e:
                    st.error(f"Error fetching variables: {e}")
            
            variable = st.selectbox("Select Variable", common_variables if common_variables else ["Temperature"])
            
        else:
            # Single location select
            location = st.selectbox(
                "Select Location",
                st.session_state.locations,
                index=0
            )
            
            # Get variables for selected location
            variables = []
            try:
                response = requests.get(f"{API_URL}/api/variables/{location}")
                if response.status_code == 200:
                    variables = response.json()['variables']
            except Exception as e:
                st.error(f"Error fetching variables: {e}")
                
            variable = st.selectbox("Select Variable", variables if variables else ["Temperature"])
        
        title = st.text_input("Visualization Title", placeholder="Optional custom title")
        
        generate_button = st.form_submit_button("Generate Visualization")
        
        if generate_button:
            try:
                if viz_type == "Time Series":
                    response = requests.post(
                        f"{API_URL}/api/visualize/time_series",
                        json={
                            'type': 'time_series',
                            'location': location,
                            'variable': variable,
                            'title': title
                        }
                    )
                elif viz_type == "Distribution":
                    response = requests.post(
                        f"{API_URL}/api/visualize/distribution",
                        json={
                            'type': 'distribution',
                            'location': location,
                            'variable': variable,
                            'title': title
                        }
                    )
                elif viz_type == "Comparison":
                    response = requests.post(
                        f"{API_URL}/api/visualize/comparison",
                        json={
                            'locations': locations,
                            'variable': variable,
                            'title': title
                        }
                    )
                
                if response.status_code == 200:
                    viz_data = response.json()['visualization']
                    fig = go.Figure(viz_data)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Error generating visualization: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("BioSphere 2 Data Explorer | Built for the Hackathon")