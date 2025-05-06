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
    proteus_available: bool = False
    
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
        
        # Check if Proteus is available
        self.proteus_available = self._check_proteus_available()
        if not self.proteus_available:
            print("WARNING: Proteus simulator not found. Simulation will be simulated.")
    
    def _check_proteus_available(self) -> bool:
        """Check if Proteus is available"""
        if os.path.exists(self.proteus_path):
            print(f"Proteus found at: {self.proteus_path}")
            return True
        
        # Try to find Proteus in common locations
        common_locations = [
            "C:/Program Files (x86)/Labcenter Electronics/Proteus 8 Professional/BIN/PDS.EXE",
            "C:/Program Files/Labcenter Electronics/Proteus 8 Professional/BIN/PDS.EXE",
            "/Applications/Proteus 8 Professional/BIN/PDS.app",
            "/usr/local/bin/proteus"
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                self.proteus_path = location
                print(f"Proteus found at: {self.proteus_path}")
                return True
        
        return False
    
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
            try:
                input_data = json.loads(input_str)
            except json.JSONDecodeError:
                return json.dumps({
                    "success": False,
                    "message": "Invalid input format",
                    "error": "Input is not a valid JSON string"
                }, indent=2)
                
            netlist = input_data.get("netlist", {})
            firmware_hex = input_data.get("firmware_hex", "")
            
            # Validate input
            if not netlist:
                return json.dumps({
                    "success": False,
                    "message": "Missing required fields",
                    "error": "Invalid input: netlist is required"
                }, indent=2)
            
            # Check if firmware hex file exists - if not provided, use a dummy one for simulation
            if not firmware_hex:
                # Fall back to a default hex file if available, otherwise generate a message
                default_hex = os.path.join(self.output_dir, "default_firmware.hex")
                if os.path.exists(default_hex):
                    firmware_hex = default_hex
                    print(f"No firmware specified, using default: {default_hex}")
                else:
                    # Generate a simple dummy hex file
                    firmware_hex = os.path.join(self.output_dir, "dummy_firmware.hex")
                    with open(firmware_hex, 'w') as f:
                        f.write(":100000000200300000000000000000000000000000C6\n:00000001FF\n")
                    print(f"No firmware specified, created dummy hex: {firmware_hex}")
            elif not os.path.exists(firmware_hex):
                return json.dumps({
                    "success": False,
                    "message": "File not found",
                    "error": f"Firmware HEX file not found: {firmware_hex}"
                }, indent=2)
            
            # Check if Proteus is available - no need to return error, we'll use simulation
            if not self.proteus_available:
                print("Proteus simulator not found. Using simulated results.")
            
            # Prepare simulation files
            sim_id = str(int(time.time()))
            dsn_file = f"sim_{sim_id}.dsn"
            dsn_path = os.path.join(self.output_dir, dsn_file)
            sim_output_path = os.path.join(self.output_dir, f"sim_results_{sim_id}.json")
            
            # Save netlist for reference
            netlist_path = os.path.join(self.output_dir, f"netlist_{sim_id}.json")
            with open(netlist_path, 'w') as f:
                json.dump(netlist, f, indent=2)
            
            # Call the update_proteus.py script to create the design file or simulate
            result = self._run_proteus_simulation(netlist, firmware_hex, dsn_path, sim_output_path, sim_id)
            
            # 构建标准化的输出结构
            if result.get("success", False):
                return json.dumps({
                    "success": True,
                    "message": f"Simulation completed successfully with ID {sim_id}",
                    "data": result
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "message": "Simulation failed", 
                    "error": result.get("error", "Unknown error during simulation")
                }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "success": False,
                "message": "Error during simulation",
                "error": str(e)
            }, indent=2)
    
    def _run_proteus_simulation(self, netlist, firmware_hex, dsn_path, sim_output_path, sim_id):
        """Run the simulation using Proteus"""
        try:
            # Check if we can simulate, else fallback to mock simulation
            if not self.proteus_available:
                return self._simulate_proteus_results(netlist, firmware_hex, sim_id)
                
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
                return {
                    "success": False,
                    "error": f"Failed to create Proteus design file: {update_process.stderr}"
                }
            
            # Run the simulation using the batch script
            bat_script_path = os.path.join(self.scripts_dir, "run_simulation.bat")
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
                return {
                    "success": False,
                    "error": f"Simulation failed: {sim_process.stderr}",
                    "stdout": sim_process.stdout
                }
            
            # Read simulation results
            with open(sim_output_path, 'r') as f:
                sim_results = json.load(f)
            
            return {
                "success": True,
                "simulation_id": sim_id,
                "dsn_file": dsn_path,
                "results": sim_results
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error during Proteus simulation: {str(e)}"
            }
            
    def _simulate_proteus_results(self, netlist, firmware_hex, sim_id):
        """Generate simulated results when Proteus is not available"""
        try:
            components = netlist.get("components", [])
            mcu = None
            leds = []
            sensors = []
            
            # Find key components
            for comp in components:
                comp_type = comp.get("type", "").upper()
                if "AT89C51" in comp_type or "8051" in comp_type or comp_type == "MCU" or comp_type == "MICROCONTROLLER":
                    mcu = comp
                elif comp_type == "LED":
                    leds.append(comp)
                elif "SENSOR" in comp_type:
                    sensors.append(comp)
            
            # Generate mock simulation results
            sim_results = {
                "success": True,
                "simulation_id": sim_id,
                "note": "This is a simulated result as Proteus is not available",
                "results": {
                    "duration_ms": 5000,
                    "completed": True,
                    "mcu_state": {
                        "registers": {
                            "ACC": "0x00",
                            "B": "0x00",
                            "PSW": "0x00",
                            "SP": "0x07"
                        },
                        "memory": {
                            "internal_ram": "0x00, 0x00, ...",
                            "sfr": "0x00, 0x00, ..."
                        }
                    },
                    "port_states": {
                        "P0": "0xFF",
                        "P1": "0xFF",
                        "P2": "0xFF", 
                        "P3": "0xFF"
                    }
                }
            }
            
            # Add LED states
            if leds:
                sim_results["results"]["led_states"] = {}
                for i, led in enumerate(leds):
                    # Simulate LED blinking
                    sim_results["results"]["led_states"][led.get("id", f"LED{i+1}")] = "ON" if i % 2 == 0 else "OFF"
            
            # Add sensor readings
            if sensors:
                sim_results["results"]["sensor_readings"] = {}
                for i, sensor in enumerate(sensors):
                    sensor_id = sensor.get("id", f"SENSOR{i+1}")
                    sensor_type = sensor.get("type", "").upper()
                    
                    if "TEMP" in sensor_type or "LM35" in sensor_type:
                        sim_results["results"]["sensor_readings"][sensor_id] = "25.5°C"
                    elif "LIGHT" in sensor_type or "LDR" in sensor_type:
                        sim_results["results"]["sensor_readings"][sensor_id] = "450 lux"
                    elif "HUMID" in sensor_type or "DHT" in sensor_type:
                        sim_results["results"]["sensor_readings"][sensor_id] = "45% RH"
                    else:
                        sim_results["results"]["sensor_readings"][sensor_id] = "1.25V"
            
            return sim_results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating simulated results: {str(e)}"
            }
    
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
