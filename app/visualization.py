import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import numpy as np
from pathlib import Path
import os
import plotly.express as px
import plotly.graph_objects as go
import json

class Visualizer:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        
    def create_time_series(self, location, variable, title=None, format='plotly_json'):
        """Create a time series visualization"""
        # Load data
        data = self.data_loader.load_data(location, variable)
        if data is None or data.empty:
            return None
            
        # Identify timestamp column
        timestamp_col = 'timestamp'
        if timestamp_col not in data.columns:
            timestamp_candidates = [col for col in data.columns if 'time' in col.lower() or 'date' in col.lower()]
            if timestamp_candidates:
                timestamp_col = timestamp_candidates[0]
            else:
                # Use first column as timestamp
                timestamp_col = data.columns[0]
                
        # Make sure timestamp is datetime
        try:
            data[timestamp_col] = pd.to_datetime(data[timestamp_col])
        except:
            pass
            
        # Identify data columns (non-timestamp columns)
        data_cols = [col for col in data.columns if col != timestamp_col]
        
        if not data_cols:
            return None
            
        # Create plot
        if format == 'plotly_json':
            # Create Plotly figure
            fig = go.Figure()
            
            for col in data_cols:
                fig.add_trace(go.Scatter(
                    x=data[timestamp_col],
                    y=data[col],
                    name=col
                ))
                
            # Update layout
            fig.update_layout(
                title=title or f"{variable} in {location}",
                xaxis_title="Time",
                yaxis_title=variable
            )
            
            # Convert to JSON
            return json.loads(fig.to_json())
            
        elif format == 'base64':
            # Create Matplotlib figure
            plt.figure(figsize=(10, 6))
            
            for col in data_cols:
                plt.plot(data[timestamp_col], data[col], label=col)
                
            plt.title(title or f"{variable} in {location}")
            plt.xlabel("Time")
            plt.ylabel(variable)
            plt.legend()
            plt.grid(True)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            return f"data:image/png;base64,{img_str}"
            
        return None
        
    def create_comparison(self, locations, variable, title=None, format='plotly_json'):
        """Create a comparison visualization across locations"""
        all_data = []
        
        for location in locations:
            data = self.data_loader.load_data(location, variable)
            if data is None or data.empty:
                continue
                
            # Identify timestamp column
            timestamp_col = 'timestamp'
            if timestamp_col not in data.columns:
                timestamp_candidates = [col for col in data.columns if 'time' in col.lower() or 'date' in col.lower()]
                if timestamp_candidates:
                    timestamp_col = timestamp_candidates[0]
                else:
                    # Use first column as timestamp
                    timestamp_col = data.columns[0]
                    
            # Make sure timestamp is datetime
            try:
                data[timestamp_col] = pd.to_datetime(data[timestamp_col])
            except:
                pass
                
            # Identify data columns (non-timestamp columns)
            data_cols = [col for col in data.columns if col != timestamp_col]
            
            if not data_cols:
                continue
                
            # Use first data column
            col = data_cols[0]
            
            # Add to all_data list with location label
            temp_df = pd.DataFrame({
                'timestamp': data[timestamp_col],
                'value': data[col],
                'location': location
            })
            all_data.append(temp_df)
            
        if not all_data:
            return None
            
        # Combine all data
        combined_data = pd.concat(all_data)
        
        # Create plot
        if format == 'plotly_json':
            # Create Plotly figure
            fig = px.line(
                combined_data, 
                x='timestamp', 
                y='value', 
                color='location',
                title=title or f"Comparison of {variable} across locations"
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title=variable
            )
            
            # Convert to JSON
            return json.loads(fig.to_json())
            
        elif format == 'base64':
            # Create Matplotlib figure
            plt.figure(figsize=(10, 6))
            
            for location in combined_data['location'].unique():
                subset = combined_data[combined_data['location'] == location]
                plt.plot(subset['timestamp'], subset['value'], label=location)
                
            plt.title(title or f"Comparison of {variable} across locations")
            plt.xlabel("Time")
            plt.ylabel(variable)
            plt.legend()
            plt.grid(True)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            return f"data:image/png;base64,{img_str}"
            
        return None
        
    def create_distribution(self, location, variable, title=None, format='plotly_json'):
        """Create a distribution visualization"""
        # Load data
        data = self.data_loader.load_data(location, variable)
        if data is None or data.empty:
            return None
            
        # Identify data columns (non-timestamp columns)
        data_cols = [col for col in data.columns if 'time' not in col.lower() and 'date' not in col.lower()]
        
        if not data_cols:
            return None
            
        # Create plot
        if format == 'plotly_json':
            # Create Plotly figure
            fig = go.Figure()
            
            for col in data_cols:
                fig.add_trace(go.Histogram(
                    x=data[col],
                    name=col,
                    opacity=0.7,
                    nbinsx=30
                ))
                
            # Update layout
            fig.update_layout(
                title=title or f"Distribution of {variable} in {location}",
                xaxis_title=variable,
                yaxis_title="Frequency",
                barmode='overlay'
            )
            
            # Convert to JSON
            return json.loads(fig.to_json())
            
        elif format == 'base64':
            # Create Matplotlib figure
            plt.figure(figsize=(10, 6))
            
            for col in data_cols:
                plt.hist(data[col].dropna(), alpha=0.7, bins=30, label=col)
                
            plt.title(title or f"Distribution of {variable} in {location}")
            plt.xlabel(variable)
            plt.ylabel("Frequency")
            plt.legend()
            plt.grid(True)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            return f"data:image/png;base64,{img_str}"
            
        return None
        
    def suggest_visualizations(self, query, agent_name=None):
        """Suggest visualizations based on a query"""
        suggestions = []
        
        # Extract location and variable from query
        locations = self.data_loader.get_locations()
        query_lower = query.lower()
        
        found_locations = []
        for location in locations:
            if location.lower() in query_lower:
                found_locations.append(location)
                
        # If agent_name is provided, add it to found locations
        if agent_name and agent_name in locations and agent_name not in found_locations:
            found_locations.append(agent_name)
            
        # If no locations found, use the agent's location or all locations
        if not found_locations:
            if agent_name and agent_name in locations:
                found_locations = [agent_name]
            else:
                found_locations = locations
                
        # Find mentioned variables
        all_variables = set()
        for location in locations:
            all_variables.update(self.data_loader.get_variables(location))
            
        found_variables = []
        for variable in all_variables:
            if variable.lower() in query_lower:
                found_variables.append(variable)
                
        # Handle common synonyms
        if 'temp' in query_lower:
            if 'Temperature' not in found_variables:
                found_variables.append('Temperature')
                
        if 'humidity' in query_lower:
            if 'Relative humidity' not in found_variables:
                found_variables.append('Relative humidity')
                
        if 'co2' in query_lower or 'carbon dioxide' in query_lower:
            if 'Carbon dioxide' not in found_variables:
                found_variables.append('Carbon dioxide')
                
        # If no variables found, suggest common ones
        if not found_variables:
            found_variables = ['Temperature', 'Relative humidity']
            
        # Generate suggestions
        if len(found_locations) == 1:
            # Single location suggestions
            location = found_locations[0]
            
            for variable in found_variables:
                if variable in self.data_loader.get_variables(location):
                    suggestions.append({
                        'type': 'time_series',
                        'location': location,
                        'variable': variable,
                        'title': f"{variable} over time in {location}",
                        'description': f"Time series of {variable} measurements in the {location} biome"
                    })
                    
                    suggestions.append({
                        'type': 'distribution',
                        'location': location,
                        'variable': variable,
                        'title': f"Distribution of {variable} in {location}",
                        'description': f"Histogram showing the distribution of {variable} values in the {location} biome"
                    })
        elif len(found_locations) > 1:
            # Multiple location suggestions
            for variable in found_variables:
                # Check if variable is available in all locations
                available_locations = [loc for loc in found_locations if variable in self.data_loader.get_variables(loc)]
                
                if len(available_locations) > 1:
                    suggestions.append({
                        'type': 'comparison',
                        'locations': available_locations,
                        'variable': variable,
                        'title': f"Comparison of {variable} across different biomes",
                        'description': f"Comparative visualization of {variable} measurements across {', '.join(available_locations)} biomes"
                    })
                    
        return suggestions[:3]  