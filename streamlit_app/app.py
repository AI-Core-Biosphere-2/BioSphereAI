import streamlit as st
import requests
import json
import plotly.graph_objects as go
import pandas as pd
from PIL import Image
import base64
import io

# API endpoints
API_URL = "http://localhost:8000"

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
    
if 'locations' not in st.session_state:
    # Get locations from API
    try:
        response = requests.get(f"{API_URL}/api/locations")
        st.session_state.locations = response.json()['locations']
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
    
    # Display environment image
    if st.session_state.current_agent and st.session_state.current_agent != "General":
        try:
            response = requests.post(
                f"{API_URL}/api/generate_image",
                json={'location': st.session_state.current_agent}
            )
            
            if response.status_code == 200:
                image_data = response.json()['image']
                image_bytes = base64.b64decode(image_data.split(",")[1])
                image = Image.open(io.BytesIO(image_bytes))
                st.image(image, caption=f"{st.session_state.current_agent} Biome")
        except Exception as e:
            st.warning(f"Could not load environment image: {e}")
    
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