import requests
import json
from app.rag import RAGSystem

class Agent:
    def __init__(self, name, description, data_loader, rag_system):
        self.name = name
        self.description = description
        self.data_loader = data_loader
        self.rag_system = rag_system
        self.conversation_history = []
        
    def get_system_prompt(self):
        return f"""You are an expert on the BioSphere 2 {self.name} biome.
{self.description}
Answer questions about the {self.name} environment and its data.
IMPORTANT: Always use the actual data provided in the context to answer questions. Never make up or guess values.
If the data is not available in the context, say "I don't have enough data to answer that question" rather than making assumptions.
Be precise and scientific in your responses."""
        
    def get_conversation_context(self):
        """Get formatted conversation history"""
        if not self.conversation_history:
            return ""
            
        formatted = []
        for entry in self.conversation_history[-5:]:  # Keep last 5 messages for context
            formatted.append(f"User: {entry['user']}")
            if 'assistant' in entry:
                formatted.append(f"Assistant: {entry['assistant']}")
                
        return "\n".join(formatted)
    
    def query(self, user_message):
        """Process a user query"""
        # Add to conversation history
        self.conversation_history.append({'user': user_message})
        
        # Get relevant context from RAG
        context = self.rag_system.get_context_for_query(user_message, location=self.name)
        
        # Build the prompt
        system_prompt = self.get_system_prompt()
        conversation_context = self.get_conversation_context()
        
        # Format the full prompt
        prompt = f"{system_prompt}\n\nRelevant Data:\n{context}\n\nConversation History:\n{conversation_context}\n\nUser: {user_message}\nAssistant:"
        
        print(f"\nAgent Debug - Full prompt:\n{prompt}")
        
        try:
            # Make request to Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'Sorry, I could not generate a response.')
                
                print(f"\nAgent Debug - Model response:\n{answer}")
                
                # Add to conversation history
                self.conversation_history[-1]['assistant'] = answer
                
                return answer
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                print(error_msg)
                return f"I'm having trouble connecting to my knowledge base. Please try again later. ({error_msg})"
                
        except Exception as e:
            print(f"Error querying Ollama: {e}")
            return "I'm having technical difficulties. Please try again later."

class AgentSystem:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.rag_system = RAGSystem(data_loader)
        self.rag_system.initialize()
        
        # Create agents for each biome
        self.agents = {
            'Desert': Agent('Desert', 
                        "The Desert biome in BioSphere 2 is a hot, arid environment with low precipitation and high temperature variability.", 
                        data_loader, self.rag_system),
                        
            'Rainforest': Agent('Rainforest', 
                            "The Rainforest biome in BioSphere 2 is a humid, tropical environment with diverse plant species and complex vertical stratification.", 
                            data_loader, self.rag_system),
                            
            # agents.py (continued)
            'Ocean': Agent('Ocean', 
                        "The Ocean biome in BioSphere 2 is a saltwater environment with a coral reef ecosystem, containing various marine organisms.", 
                        data_loader, self.rag_system),
                        
            'LEO-W': Agent('LEO-W', 
                        "The LEO-W (Landscape Evolution Observatory - West) is a controlled environment for studying how landscapes evolve under different conditions.", 
                        data_loader, self.rag_system)
        }
        
    def get_agent_for_location(self, location):
        """Get the agent for a specific location"""
        return self.agents.get(location)
        
    def get_all_agents(self):
        """Get all available agents"""
        return self.agents
        
    def route_query(self, query, location=None):
        """Route a query to the appropriate agent"""
        if location and location in self.agents:
            return self.agents[location].query(query)
            
        # Identify the best agent based on query content
        best_location = self._identify_location_from_query(query)
        
        if best_location:
            return self.agents[best_location].query(query)
        else:
            # Default to a general response
            return self._generate_general_response(query)
            
    def _identify_location_from_query(self, query):
        """Identify the location from the query"""
        # Simple keyword matching
        query_lower = query.lower()
        
        for location in self.agents:
            if location.lower() in query_lower:
                return location
                
        # Use RAG to try to identify the most relevant location
        results = self.rag_system.query(query, top_k=2)
        if results:
            locations = [doc.get('location') for doc in results if 'location' in doc]
            if locations:
                # Return the most common location
                from collections import Counter
                return Counter(locations).most_common(1)[0][0]
                
        return None
        
    def _generate_general_response(self, query):
        """Generate a general response when no specific agent is identified"""
        # Build a generic system prompt
        system_prompt = """You are an expert on BioSphere 2, a large-scale Earth system science research facility.
It contains several biomes including Desert, Rainforest, Ocean, and LEO-W.
Answer general questions about BioSphere 2 and suggest which specific biome might have more detailed information."""
        
        # Get relevant context from RAG
        context = self.rag_system.get_context_for_query(query)
        
        # Format the full prompt
        prompt = f"{system_prompt}\n\nRelevant Data:\n{context}\n\nUser: {query}\nAssistant:"
        
        try:
            # Make request to Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Sorry, I could not generate a response.')
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                print(error_msg)
                return f"I'm having trouble connecting to my knowledge base. Please try again later. ({error_msg})"
                
        except Exception as e:
            print(f"Error querying Ollama: {e}")
            return "I'm having technical difficulties. Please try again later."