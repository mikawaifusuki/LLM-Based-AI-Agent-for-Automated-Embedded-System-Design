import os
import subprocess
import json
import time
from typing import Dict, List, Optional, Any, Union
import shutil

from langchain.tools.base import BaseTool

class SimulatorTool(BaseTool):
    """Tool for simulating 8051 circuits using Proteus."""
    
    name: str = "SimulatorTool"
    description: str = """
    Use this tool to simulate a circuit design in Proteus.
    Input should be a JSON object with circuit netlist and firmware hex path.
    Returns simulation results including voltages, logic analyzer data, or UART output.
    """
    
    output_dir: str = "backend/outputs"
    scripts_dir: str = "backend/scripts"
    template_dsn_path: str = "backend/scripts/template.dsn"
    proteus_path: str = "C:/Program Files (x86)/Labcenter Electronics/Proteus 8 Professional/BIN/PDS.EXE"
    
    def __init__(
        self, 
        output_dir: Optional[str] = None,
        scripts_dir: Optional[str] = None,
        template_dsn_path: Optional[str] = None,
        proteus_path: Optional[str] = None
    ):
        """Initialize the simulator tool.
        
        Args:
            output_dir: Directory where simulation results will be stored.
            scripts_dir: Directory containing simulator scripts.
            template_dsn_path: Path to the template Proteus design file.
            proteus_path: Path to the Proteus executable.
        """
        super().__init__()
        
        if output_dir:
            self.output_dir = output_dir
        if scripts_dir:
            self.scripts_dir = scripts_dir
        if template_dsn_path:
            self.template_dsn_path = template_dsn_path
        if proteus_path:
            self.proteus_path = proteus_path
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _tool_run(self, input_str: str) -> str:
        """Run the simulator tool.
        
        Args:
            input_str: JSON string with netlist and firmware path.
                Format: 
                {
                    "netlist": {
                        "components": [
                            {"type": "AT89C51", "id": "U1", "position": {"x": 100, "y": 100}, "connections": {...}},
                            ...
                        ],
                        "connections": [
                            {"from": {"component": "U1", "pin": "P1.0"}, "to": {"component": "LED1", "pin": "Anode"}},
                            ...
                        ]
                    },
                    "firmware_hex": "path/to/firmware.hex"
                }
            
        Returns:
            JSON string with simulation results.
        """
        try:
            # Parse input
            input_data = json.loads(input_str)
            netlist = input_data.get("netlist", {})
            firmware_hex = input_data.get("firmware_hex", "")
            
            # Validate input
            if not netlist or not firmware_hex:
                return json.dumps({
                    "success": False,
                    "error": "Invalid input: netlist and firmware_hex are required"
                })
            
            # Prepare simulation files
            sim_id = str(int(time.time()))
            dsn_file = f"sim_{sim_id}.dsn"
            dsn_path = os.path.join(self.output_dir, dsn_file)
            
            # Call the update_proteus.py script to create the design file
            script_path = os.path.join(self.scripts_dir, "update_proteus.py")
            update_cmd = [
                "python", script_path, 
                "--template", self.template_dsn_path,
                "--output", dsn_path,
                "--netlist", json.dumps(netlist),
                "--firmware", firmware_hex
            ]
            
            update_process = subprocess.run(
                update_cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if update_process.returncode != 0:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to create Proteus design file: {update_process.stderr}"
                })
            
            # Run the simulation using the batch script
            bat_script_path = os.path.join(self.scripts_dir, "run_simulation.bat")
            sim_output_path = os.path.join(self.output_dir, f"sim_results_{sim_id}.json")
            
            sim_cmd = [
                bat_script_path,
                self.proteus_path,
                dsn_path,
                sim_output_path
            ]
            
            sim_process = subprocess.run(
                sim_cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if simulation completed successfully
            if sim_process.returncode != 0 or not os.path.exists(sim_output_path):
                return json.dumps({
                    "success": False,
                    "error": f"Simulation failed: {sim_process.stderr}",
                    "stdout": sim_process.stdout
                })
            
            # Read simulation results
            with open(sim_output_path, 'r') as f:
                sim_results = json.load(f)
            
            return json.dumps({
                "success": True,
                "simulation_id": sim_id,
                "dsn_file": dsn_path,
                "results": sim_results
            }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error during simulation: {str(e)}"
            }, indent=2)
    
    # For compatibility with langchain newer versions
    def _run(self, input_str: str) -> str:
        return self._tool_run(input_str)


def run_simulation(netlist: Dict, firmware_hex: str) -> Dict:
    """Run a simulation with the given netlist and firmware.
    
    Args:
        netlist: Dictionary with component and connection information.
        firmware_hex: Path to the compiled firmware HEX file.
        
    Returns:
        Dictionary with simulation results.
    """
    simulator_tool = SimulatorTool()
    input_data = {
        "netlist": netlist,
        "firmware_hex": firmware_hex
    }
    result_json = simulator_tool._tool_run(json.dumps(input_data))
    return json.loads(result_json)


if __name__ == "__main__":
    # Example usage
    netlist = {
        "components": [
            {
                "type": "AT89C51",
                "id": "U1",
                "position": {"x": 100, "y": 100},
                "connections": {
                    "P1.0": "LED1.Anode",
                    "VCC": "VCC",
                    "GND": "GND",
                    "XTAL1": "XTAL1.Terminal1",
                    "XTAL2": "XTAL1.Terminal2"
                }
            },
            {
                "type": "LED",
                "id": "LED1",
                "position": {"x": 200, "y": 100},
                "connections": {
                    "Cathode": "R1.Terminal1"
                }
            },
            {
                "type": "Resistor",
                "id": "R1",
                "value": "220",
                "position": {"x": 200, "y": 150},
                "connections": {
                    "Terminal2": "GND"
                }
            },
            {
                "type": "Crystal",
                "id": "XTAL1",
                "value": "11.0592MHz",
                "position": {"x": 50, "y": 100}
            }
        ]
    }
    
    firmware_hex = "backend/outputs/firmware.hex"
    
    result = run_simulation(netlist, firmware_hex)
    print(json.dumps(result, indent=2))
