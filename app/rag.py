import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pickle
import os

class RAGSystem:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.documents = []
        self.initialized = False
        
    def initialize(self):
        """Initialize the RAG system by creating documents from metadata"""
        if self.initialized:
            return
            
        print("Initializing RAG system...")
        
        # Create documents from metadata
        self._create_documents()
        
        # Create FAISS index
        self._create_index()
        
        self.initialized = True
        print(f"RAG system initialized with {len(self.documents)} documents")
        
    def _create_documents(self):
        """Create documents from metadata and variable information"""
        documents = []
        
        # Add general location information
        for location in self.data_loader.get_locations():
            doc = f"Location: {location}. "
            doc += f"Variables available: {', '.join(self.data_loader.get_variables(location))}. "
            
            # Add timeframe if available
            timeframe = self.data_loader.get_data_timeframe(location)
            if timeframe:
                doc += f"Data available from {timeframe['start']} to {timeframe['end']}."
                
            documents.append({
                'content': doc,
                'location': location,
                'type': 'location_info'
            })
            
            # Add variable-specific documents
            for variable in self.data_loader.get_variables(location):
                summary = self.data_loader.get_variable_summary(location, variable)
                if summary:
                    for col, stats in summary.items():
                        # Handle both numpy.float64 and pandas Series values
                        mean_val = float(stats['mean'].mean() if hasattr(stats['mean'], 'mean') else stats['mean'])
                        min_val = float(stats['min'].min() if hasattr(stats['min'], 'min') else stats['min'])
                        max_val = float(stats['max'].max() if hasattr(stats['max'], 'max') else stats['max'])
                        std_val = float(stats['std'].mean() if hasattr(stats['std'], 'mean') else stats['std'])
                        
                        doc = f"Variable: {variable} ({col}) in {location}. "
                        doc += f"Mean value: {mean_val:.2f}, "
                        doc += f"Range: {min_val:.2f} to {max_val:.2f}, "
                        doc += f"Standard deviation: {std_val:.2f}."
                        
                        documents.append({
                            'content': doc,
                            'location': location,
                            'variable': variable,
                            'column': col,
                            'type': 'variable_info'
                        })
        
        self.documents = documents
        
    def _create_index(self):
        """Create FAISS index from documents"""
        if not self.documents:
            return
            
        # Extract content for embedding
        texts = [doc['content'] for doc in self.documents]
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        
    def query(self, query_text, top_k=5):
        """Query the RAG system"""
        if not self.initialized:
            self.initialize()
            
        if not self.index:
            return []
            
        # Generate query embedding
        query_embedding = self.model.encode([query_text])
        
        # Search FAISS index
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)
        
        # Retrieve matching documents
        results = []
        for idx in indices[0]:
            if idx < len(self.documents):
                results.append(self.documents[idx])
                
        return results
    
    def get_context_for_query(self, query, location=None):
        """Get context for a query, optionally filtered by location"""
        results = self.query(query, top_k=5)
        
        # Filter by location if specified
        if location:
            results = [doc for doc in results if doc.get('location') == location]
            
        # Extract context
        context = "\n".join([doc['content'] for doc in results])
        
        return context