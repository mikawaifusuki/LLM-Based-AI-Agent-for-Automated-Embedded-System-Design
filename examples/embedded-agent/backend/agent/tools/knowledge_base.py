import json
import os
from typing import Dict, List, Optional, Any

import faiss
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from langchain.tools import BaseTool
from langchain.vectorstores import FAISS
from langchain.schema import Document

class KnowledgeBaseTool(BaseTool):
    """Tool for retrieving component information from the knowledge base."""
    
    name = "KnowledgeBaseTool"
    description = """
    Use this tool to retrieve information about electronic components.
    Input should be a query string describing the component or its function.
    Returns structured information about matching components.
    """
    
    knowledge_base: FAISS = None
    components_data: List[Dict[str, Any]] = []
    
    def __init__(self, kb_path: str = "backend/kb/components.jsonl"):
        """Initialize the knowledge base tool.
        
        Args:
            kb_path: Path to the knowledge base JSONL file.
        """
        super().__init__()
        self.kb_path = kb_path
        self._load_components()
        self._initialize_vector_store()
    
    def _load_components(self) -> None:
        """Load component data from the knowledge base file."""
        self.components_data = []
        try:
            with open(self.kb_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        self.components_data.append(json.loads(line))
        except Exception as e:
            print(f"Error loading components data: {e}")
    
    def _initialize_vector_store(self) -> None:
        """Initialize the FAISS vector store with component data."""
        try:
            # Create documents for FAISS
            documents = []
            for i, component in enumerate(self.components_data):
                # Create a searchable text representation of the component
                text = f"Name: {component['name']}\n"
                text += f"Type: {component['type']}\n"
                text += f"Subtype: {component.get('subtype', '')}\n"
                text += f"Interface: {component.get('interface', '')}\n"
                text += f"Notes: {component.get('notes', '')}\n"
                
                # Add document with metadata for retrieval
                doc = Document(page_content=text, metadata={"index": i})
                documents.append(doc)
            
            # Create FAISS vector store
            embeddings = OpenAIEmbeddings()
            self.knowledge_base = FAISS.from_documents(documents, embeddings)
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            self.knowledge_base = None
    
    def _tool_run(self, query: str) -> str:
        """Run the tool to retrieve component information.
        
        Args:
            query: Query string describing the component or its function.
            
        Returns:
            JSON string with component information.
        """
        if not self.knowledge_base:
            return json.dumps({"error": "Knowledge base not initialized"})
        
        try:
            # Search the vector store
            docs = self.knowledge_base.similarity_search(query, k=3)
            
            # Get the component data for the retrieved documents
            results = []
            for doc in docs:
                component_index = doc.metadata["index"]
                results.append(self.components_data[component_index])
            
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error searching knowledge base: {e}"})
    
    # For compatibility with langchain newer versions
    def _run(self, query: str) -> str:
        return self._tool_run(query)


def get_component_info(component_query: str) -> Dict:
    """Get component information from the knowledge base.
    
    Args:
        component_query: Query string describing the component or its function.
        
    Returns:
        Dictionary with component information.
    """
    kb_tool = KnowledgeBaseTool()
    result_json = kb_tool._tool_run(component_query)
    results = json.loads(result_json)
    
    # Return the first result if available
    if isinstance(results, list) and results:
        return results[0]
    elif isinstance(results, dict) and "error" not in results:
        return results
    else:
        return {"error": "No matching component found"}


if __name__ == "__main__":
    # Example usage
    query = "temperature sensor"
    result = get_component_info(query)
    print(json.dumps(result, indent=2))
