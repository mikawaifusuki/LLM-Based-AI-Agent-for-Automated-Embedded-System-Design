import json
import os
from typing import Dict, List, Optional, Any

import faiss
import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.tools.base import BaseTool
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

class KnowledgeBaseTool(BaseTool):
    """Tool for retrieving component information from the knowledge base."""
    
    name: str = "KnowledgeBaseTool"
    description: str = """
    Use this tool to retrieve information about electronic components.
    Input should be a query string describing the component or its function.
    Returns structured information about matching components.
    """
    
    knowledge_base: Optional[FAISS] = None
    components_data: List[Dict[str, Any]] = []
    kb_path: str = "backend/kb/components.jsonl"
    
    def __init__(self, kb_path: str = "kb/components.jsonl"):
        """Initialize the knowledge base tool.
        
        Args:
            kb_path: Path to the knowledge base JSONL file.
        """
        super().__init__()
        
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 计算项目根目录（去掉 /agent/tools 部分）
        project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
        
        # 构建可能的路径
        possible_paths = [
            kb_path,  # 原始路径
            os.path.join(project_root, kb_path),  # 相对于项目根目录
            os.path.join(project_root, "backend", kb_path),  # 相对于backend目录
            os.path.join(current_dir, "../../../", kb_path),  # 相对于当前文件向上3级目录
            os.path.join(current_dir, "../../../backend", kb_path)  # 相对于backend目录（另一种方式）
        ]
        
        # 创建kb目录如果不存在
        kb_dir = os.path.join(project_root, "backend/kb")
        os.makedirs(kb_dir, exist_ok=True)
        
        # 找到第一个存在的文件路径
        self.kb_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.kb_path = path
                print(f"Found knowledge base at: {self.kb_path}")
                break
        
        # 如果都找不到，使用默认路径，并创建示例文件
        if not self.kb_path:
            self.kb_path = os.path.join(project_root, "backend/kb/components.jsonl")
            print(f"Creating example knowledge base at: {self.kb_path}")
            self._create_example_kb()
        
        print(f"Using knowledge base path: {self.kb_path}")
        self._load_components()
        self._initialize_vector_store()
    
    def _create_example_kb(self) -> None:
        """创建示例知识库文件"""
        example_components = [
            {"name": "LM35", "type": "sensor", "subtype": "temperature", "pins": {"Vcc": 1, "GND": 3, "Vout": 2}, "interface": "Analog", "notes": "Temperature sensor that outputs 10mV/°C. Requires 5V supply.", "datasheet_url": "datasheets/lm35.pdf"},
            {"name": "AT89C51", "type": "microcontroller", "subtype": "8051", "pins": {"P0.0-P0.7": [32, 33, 34, 35, 36, 37, 38, 39], "P1.0-P1.7": [1, 2, 3, 4, 5, 6, 7, 8], "P2.0-P2.7": [21, 22, 23, 24, 25, 26, 27, 28], "P3.0-P3.7": [10, 11, 12, 13, 14, 15, 16, 17], "RST": 9, "ALE": 30, "EA": 31, "PSEN": 29, "XTAL1": 19, "XTAL2": 18, "VCC": 40, "GND": 20}, "interface": "Digital", "notes": "Standard 8051 microcontroller with 4KB Flash, 128 bytes RAM", "datasheet_url": "datasheets/at89c51.pdf"},
            {"name": "LED", "type": "output", "subtype": "visual", "pins": {"Anode": 1, "Cathode": 2}, "interface": "Digital", "notes": "Requires current limiting resistor, typical forward voltage 1.8-3.3V depending on color", "datasheet_url": "datasheets/led.pdf"},
            {"name": "Resistor", "type": "passive", "subtype": "resistor", "pins": {"Terminal1": 1, "Terminal2": 2}, "interface": "Passive", "notes": "Common values: 220Ω for LED current limiting, 10kΩ for pull-up/pull-down", "datasheet_url": "datasheets/resistor.pdf"},
            {"name": "Crystal", "type": "passive", "subtype": "oscillator", "pins": {"Terminal1": 1, "Terminal2": 2}, "interface": "Passive", "notes": "Typical values for 8051: 11.0592 MHz or 12 MHz", "datasheet_url": "datasheets/crystal.pdf"},
            {"name": "Capacitor", "type": "passive", "subtype": "capacitor", "pins": {"Terminal1": 1, "Terminal2": 2}, "interface": "Passive", "notes": "Typical values: 22pF for crystal circuit, 10µF for power filtering", "datasheet_url": "datasheets/capacitor.pdf"},
            {"name": "DC_Motor", "type": "output", "subtype": "motor", "pins": {"Terminal1": 1, "Terminal2": 2}, "interface": "Digital", "notes": "Typically requires driver circuit like L293D for control from microcontroller", "datasheet_url": "datasheets/dc_motor.pdf"},
            {"name": "L293D", "type": "driver", "subtype": "motor_driver", "pins": {"1,2EN": 1, "1A": 2, "1Y": 3, "GND": [4, 5, 12, 13], "2Y": 6, "2A": 7, "VCC2": 8, "3,4EN": 9, "3A": 10, "3Y": 11, "4Y": 14, "4A": 15, "VCC1": 16}, "interface": "Digital", "notes": "Dual H-bridge motor driver, can drive two DC motors, requires 5V logic supply and motor supply voltage", "datasheet_url": "datasheets/l293d.pdf"},
            {"name": "ADC0804", "type": "converter", "subtype": "analog_to_digital", "pins": {"CS": 1, "RD": 2, "WR": 3, "CLK_IN": 4, "INTR": 5, "Vin+": 6, "Vin-": 7, "AGND": 8, "Vref/2": 9, "D0-D7": [18, 17, 16, 15, 14, 13, 12, 11], "VCC": 20, "DGND": 10}, "interface": "Mixed", "notes": "8-bit ADC, can be interfaced with 8051 for analog readings like LM35 temperature sensor", "datasheet_url": "datasheets/adc0804.pdf"}
        ]
        
        os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
        with open(self.kb_path, 'w') as f:
            for component in example_components:
                f.write(json.dumps(component) + '\n')
    
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
        """Run search against the knowledge base.
        
        Args:
            query: Natural language query about components.
            
        Returns:
            JSON string with search results and information.
        """
        try:
            if not self.knowledge_base or self.knowledge_base is None or not hasattr(self.knowledge_base, 'similarity_search'):
                return json.dumps({
                    "success": False,
                    "message": "Knowledge base not initialized.",
                    "error": "Knowledge base not properly loaded or initialized."
                }, indent=2)
            
            # 使用正确的方法名 similarity_search
            docs = self.knowledge_base.similarity_search(query, k=3)
            
            # Format the results
            formatted_results = []
            for doc in docs:
                component_index = doc.metadata["index"]
                component = self.components_data[component_index]
                
                # Convert component to a more readable format
                comp_info = {
                    "type": component.get("type", "Unknown"),
                    "model": component.get("model", "Unknown"),
                    "description": component.get("description", "No description available."),
                    "pins": component.get("pins", []),
                    "specifications": component.get("specifications", {}),
                    "datasheet": component.get("datasheet", "Not available"),
                    "relevance_score": doc.metadata.get("score", 0.0)
                }
                formatted_results.append(comp_info)
            
            return json.dumps({
                "success": True,
                "message": f"Found {len(formatted_results)} results for query: {query}",
                "data": {
                    "query": query,
                    "results": formatted_results
                }
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "message": "Error searching knowledge base.",
                "error": str(e)
            }, indent=2)
    
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
