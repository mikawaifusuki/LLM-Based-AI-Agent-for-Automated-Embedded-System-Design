"""
Main agent for the 8051 embedded system design automation.
"""

import json
import os
from typing import Dict, List, Any, Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish
from langchain.chat_models import ChatOpenAI
from langchain.tools.base import BaseTool

# Import custom tools
from tools.knowledge_base import KnowledgeBaseTool
from tools.compiler import CompilerTool 
from tools.simulator import SimulatorTool


class EmbeddedDesignAgent:
    """Agent for automating the design of 8051 embedded systems."""
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        model_name: str = "gpt-4o",
        output_dir: str = "backend/outputs",
        verbose: bool = False
    ):
        """Initialize the embedded design agent.
        
        Args:
            openai_api_key: OpenAI API key.
            model_name: Name of the model to use.
            output_dir: Directory for storing outputs.
            verbose: Whether to print verbose output.
        """
        # Initialize agent components
        self.output_dir = output_dir
        self.verbose = verbose
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"),
            temperature=0.1
        )
        
        # Initialize tools
        self.knowledge_tool = KnowledgeBaseTool()
        self.compiler_tool = CompilerTool(output_dir=output_dir)
        self.simulator_tool = SimulatorTool(output_dir=output_dir)
        
        self.tools = [
            self.knowledge_tool,
            self.compiler_tool,
            self.simulator_tool
        ]
        
        # Set up memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize agent with prompt
        self.prompt = self._create_prompt()
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        
        # Set up agent executor
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=15  # Limit number of iterations to prevent infinite loops
        )
    
    def _create_prompt(self) -> PromptTemplate:
        """Create the prompt template for the agent."""
        template = """
You are an embedded system AI agent that designs 8051 microcontroller systems.
Your task is to design a complete system that includes circuit design, 8051 C code, compilation, and simulation.

Requirements: {user_request}

Follow a step-by-step process to design the system:

Step 1: Analyze the requirements and determine which components are needed.
Step 2: Query the knowledge base to get details about each component.
Step 3: Design the circuit connections (netlist).
Step 4: Write 8051 C code that implements the required functionality.
Step 5: Compile the code using the SDCC compiler.
Step 6: Simulate the design in Proteus and analyze the results.
Step 7: If there are any issues, fix them and try again.

At each step, provide your reasoning and explain what you're doing.

Remember these important details for 8051 programming:
- P0, P1, P2, and P3 are the four 8-bit ports
- Use "P1_0 = 1" syntax to set pin P1.0 high
- Timer0 and Timer1 can be used for timing operations
- ADC0804 is commonly used for analog-to-digital conversion

For circuit design:
- All ICs need VCC and GND connections
- LEDs need current-limiting resistors (typically 220Ω to 1kΩ)
- Crystal oscillator (typically 11.0592MHz) needs two 22pF capacitors

{chat_history}

Let's approach this design task step by step, making sure to explain my reasoning at each stage.

{agent_scratchpad}
"""
        
        return PromptTemplate.from_template(template)
    
    def run(self, user_request: str) -> Dict[str, Any]:
        """Run the agent on a user request.
        
        Args:
            user_request: User's request in natural language.
            
        Returns:
            Dictionary with the agent's response and any generated artifacts.
        """
        try:
            # Execute the agent
            response = self.agent_executor.run(user_request=user_request)
            
            # Gather artifacts
            artifacts = self._collect_artifacts()
            
            return {
                "success": True,
                "response": response,
                "artifacts": artifacts
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _collect_artifacts(self) -> Dict[str, str]:
        """Collect artifacts from the most recent run.
        
        Returns:
            Dictionary with paths to generated artifacts.
        """
        artifacts = {}
        
        # Check for C source file
        c_file_path = os.path.join(self.output_dir, "main.c")
        if os.path.exists(c_file_path):
            artifacts["c_source"] = c_file_path
        
        # Check for HEX file
        hex_file_path = os.path.join(self.output_dir, "firmware.hex")
        if os.path.exists(hex_file_path):
            artifacts["firmware_hex"] = hex_file_path
        
        # Check for DSN file (most recent one)
        dsn_files = [f for f in os.listdir(self.output_dir) if f.endswith(".dsn")]
        if dsn_files:
            # Sort by modification time (newest first)
            dsn_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)), reverse=True)
            artifacts["circuit_dsn"] = os.path.join(self.output_dir, dsn_files[0])
        
        # Check for simulation results
        sim_files = [f for f in os.listdir(self.output_dir) if f.startswith("sim_results_") and f.endswith(".json")]
        if sim_files:
            # Sort by modification time (newest first)
            sim_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)), reverse=True)
            artifacts["simulation_results"] = os.path.join(self.output_dir, sim_files[0])
        
        # Add netlist if it exists
        netlist_path = os.path.join(self.output_dir, "netlist.json")
        if os.path.exists(netlist_path):
            artifacts["netlist"] = netlist_path
        
        return artifacts


if __name__ == "__main__":
    # Example usage
    agent = EmbeddedDesignAgent(verbose=True)
    
    test_request = """
    Design a system that uses an 8051 microcontroller and an LM35 temperature sensor.
    The system should read the temperature once per second.
    If the temperature exceeds 30°C, turn on an LED and activate a cooling fan.
    Otherwise, keep the LED off and the fan off.
    Display the current temperature on the UART.
    """
    
    result = agent.run(test_request)
    
    if result["success"]:
        print("\nAgent Response:")
        print(result["response"])
        
        print("\nGenerated Artifacts:")
        for name, path in result["artifacts"].items():
            print(f"- {name}: {path}")
    else:
        print(f"Error: {result['error']}")
