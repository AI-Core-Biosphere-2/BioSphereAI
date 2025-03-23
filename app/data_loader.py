import pandas as pd
import os
from pathlib import Path
import numpy as np

class DataLoader:
    def __init__(self, data_dir='data/raw'):
        self.data_dir = Path(data_dir)
        self.data_cache = {}
        self.metadata = self._load_metadata()
        
    def _load_metadata(self):
        """Convert metadata to a more usable format"""
        # This is a hardcoded version of your metadata for simplicity
        locations = ['Ocean', 'Desert', 'Rainforest', 'LEO-W']
        
        # Simplified format of metadata
        metadata = {
            'Ocean': {
                'variables': ['pH', 'Temperature', 'Salinity', 'Dissolved oxygen'],
                'files': ['Ocean_FEB-2025.csv']
            },
            'Desert': {
                'variables': ['Temperature', 'Relative humidity', 'Carbon dioxide'],
                'files': ['Desert_Temp_RH_FEB-2025.csv', 'Desert_CO2_FEB-2025.csv']
            },
            'Rainforest': {
                'variables': ['Temperature', 'Relative humidity', 'Carbon dioxide', 
                             'Radiation', 'Wind speed', 'Wind direction'],
                'files': ['RF_CO2_FEB-2025.csv', 'RF_TigerPond_Temp_RH_FEB-2025.csv',
                         'RF_LowLand_Temp_RH_FEB-2025.csv', 'RF_Mountain_Temp_RH_FEB-2025.csv',
                         'RF_MountainTower_rad_at10m_FEB-2025.csv']
            },
            'LEO-W': {
                'variables': ['Air pressure', 'Carbon dioxide', 'Water vapor', 
                            'Radiation', 'Wind speed', 'Temperature', 'Relative humidity'],
                'files': ['LEO-W_PTB_Pa_hPa_FEB-2025.csv', 'LEO-W_LICOR_CO2_FEB-2025.csv',
                         'LEO-W_LICOR_H2O_FEB-2025.csv', 'LEO-W_CNR4_LEO-W_10_-2_0_rad_FEB-2025.csv']
            }
        }
        
        return metadata
    
    def get_locations(self):
        """Return list of available locations"""
        return list(self.metadata.keys())
    
    def get_variables(self, location):
        """Return list of variables for a specific location"""
        if location in self.metadata:
            return self.metadata[location]['variables']
        return []
    
    def load_data(self, location, variable=None):
        """Load data for a specific location and optionally filter by variable"""
        if location not in self.metadata:
            return None
            
        # Check if data is already cached
        cache_key = f"{location}_{variable if variable else 'all'}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
            
        # Load all files for this location
        all_data = []
        for file_name in self.metadata[location]['files']:
            try:
                file_path = self.data_dir / file_name
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    
                    # Identify datetime column (assuming first column is datetime)
                    if 'timestamp' not in df.columns and 'date' not in df.columns.str.lower() and 'time' not in df.columns.str.lower():
                        df.rename(columns={df.columns[0]: 'timestamp'}, inplace=True)
                    
                    all_data.append(df)
            except Exception as e:
                print(f"Error loading {file_name}: {e}")
                
        if not all_data:
            return None
            
        # Try to merge data frames if possible, otherwise return list
        try:
            if len(all_data) > 1:
                # Attempt to merge on timestamp or similar column
                merged_data = pd.concat(all_data, axis=1)
                # Drop duplicate columns, keeping the first occurrence
                merged_data = merged_data.loc[:, ~merged_data.columns.duplicated()]
            else:
                merged_data = all_data[0]
                
            # Filter by variable if specified
            if variable and variable in self.metadata[location]['variables']:
                # Find columns containing the variable name
                var_cols = [col for col in merged_data.columns if variable.lower() in col.lower()]
                if var_cols:
                    filtered_data = merged_data[['timestamp'] + var_cols]
                    self.data_cache[cache_key] = filtered_data
                    return filtered_data
            
            self.data_cache[cache_key] = merged_data
            return merged_data
            
        except Exception as e:
            print(f"Error processing data: {e}")
            return all_data
    
    def get_variable_summary(self, location, variable):
        """Get summary statistics for a specific variable"""
        data = self.load_data(location, variable)
        if data is None:
            return None
            
        # Extract variable columns (excluding timestamp)
        var_cols = [col for col in data.columns if col != 'timestamp']
        
        summary = {}
        for col in var_cols:
            try:
                summary[col] = {
                    'mean': data[col].mean(),
                    'min': data[col].min(),
                    'max': data[col].max(),
                    'std': data[col].std()
                }
            except:
                pass
                
        return summary
    
    def get_data_timeframe(self, location):
        """Get the date range for data at the location"""
        data = self.load_data(location)
        if data is None or 'timestamp' not in data.columns:
            return None
            
        try:
            # Convert to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                
            return {
                'start': data['timestamp'].min(),
                'end': data['timestamp'].max()
            }
        except:
            return None