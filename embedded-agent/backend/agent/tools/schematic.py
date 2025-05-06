"""
Schematic Tool for 8051 Embedded Design Agent.

This tool generates circuit schematics based on netlist information provided in JSON format.
It supports both visual (using matplotlib) and text-based schematic generation.

Connection Format:
---------------
The tool supports flexible connection formats to handle various schematic description needs:

1. Basic string format: "component.pin"
   Example: {"from": "crystal.1", "to": "8051.XTAL1"}

2. Multiple pin connections using comma-separated strings:
   Example: {"from": "crystal.1", "to": "8051.XTAL1, 8051.XTAL2"}
   This will be expanded into multiple individual connections.

3. Dictionary format:
   Example: {"from": {"component": "crystal", "pin": "1"}, "to": {"component": "8051", "pin": "XTAL1"}}

4. Components without explicit pin identifiers will use pin "1" by default:
   Example: {"from": "VCC", "to": "8051.VCC"} is equivalent to {"from": "VCC.1", "to": "8051.VCC"}

5. Mixed formats:
   You can mix string and dictionary formats, as well as single and multiple connections.

Error Handling:
-------------
The tool provides detailed error messages for invalid inputs:
- Invalid JSON format
- Missing required fields
- Invalid connection format
- Processing errors

Usage:
-----
Input JSON format:
{
    "components": [
        {"id": "U1", "type": "microcontroller", "value": "8051"},
        {"id": "R1", "type": "resistor", "value": "10k"}
    ],
    "connections": [
        {"from": "U1.P1.0", "to": "R1.1"},                           # String format
        {"from": "U1.P1.1, U1.P1.2", "to": "R1.2, R2.1"},            # Multiple pins
        {"from": {"component": "U1", "pin": "P1.3"}, "to": "R2.2"}   # Dictionary format
    ]
}

Output JSON format:
{
    "success": true,
    "message": "Successfully generated schematic",
    "data": {
        "schematic_id": "...",
        "description": "...",
        "text_schematic": "...",
        "image_path": "..."
    }
}
"""

import os
import json
import time
import traceback
from typing import Dict, List, Optional, Any

from langchain.tools.base import BaseTool

class SchematicTool(BaseTool):
    """Tool for generating schematic diagrams for electronic circuits."""
    
    name: str = "SchematicTool"
    description: str = """
    Use this tool to generate schematic diagrams for electronic circuits.
    Input should be a JSON object with components and connections.
    Returns a path to the generated schematic file.
    """
    
    output_dir: str = "backend/outputs/schematics"
    has_visualization_libs: bool = False
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize schematic generation tool.
        
        Args:
            output_dir: Directory where schematic files will be saved
        """
        super().__init__()
        
        # Set default output directory if not provided
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(os.getcwd(), "outputs", "schematics")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check if necessary libraries for advanced visualization are available
        self.has_visualization_libs = self._check_visualization_libraries()
        
    def _check_visualization_libraries(self) -> bool:
        """Check if visualization libraries are available"""
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            import numpy as np
            return True
        except ImportError:
            print("WARNING: Matplotlib or NumPy not found. Will use basic visualization.")
            return False
    
    def _tool_run(self, input_str: str) -> str:
        """Generate circuit schematic based on netlist information.
        
        Args:
            input_str: JSON string containing netlist information
                Format: {
                    "components": [
                        {"id": "U1", "type": "microcontroller", "value": "ATmega328"},
                        {"id": "R1", "type": "resistor", "value": "10k"}
                    ],
                    "connections": [
                        {"from": "U1.D2", "to": "R1.1"},  # 字符串格式
                        # 或
                        {"from": {"component": "U1", "pin": "D2"}, "to": {"component": "R1", "pin": "1"}}  # 字典格式
                    ]
                }
                
        Returns:
            JSON string with generated schematic information
        """
        try:
            # Parse input
            try:
                netlist = json.loads(input_str)
            except json.JSONDecodeError as e:
                return json.dumps({
                    "success": False,
                    "message": "Invalid input format",
                    "error": f"Input is not a valid JSON string: {str(e)}"
                }, indent=2)
            
            # Validate input
            if not isinstance(netlist, dict):
                return json.dumps({
                    "success": False,
                    "message": "Invalid input format",
                    "error": "Input must be a JSON object/dictionary"
                }, indent=2)
                
            if "components" not in netlist or "connections" not in netlist:
                return json.dumps({
                    "success": False,
                    "message": "Missing required fields",
                    "error": "Invalid netlist format. Must contain 'components' and 'connections'"
                }, indent=2)
            
            # Validate components and connections are lists
            if not isinstance(netlist.get("components", []), list):
                return json.dumps({
                    "success": False,
                    "message": "Invalid components format",
                    "error": "'components' must be a list of component objects"
                }, indent=2)
                
            if not isinstance(netlist.get("connections", []), list):
                return json.dumps({
                    "success": False,
                    "message": "Invalid connections format",
                    "error": "'connections' must be a list of connection objects"
                }, indent=2)
            
            # Pre-validate connections
            for i, conn in enumerate(netlist.get("connections", [])):
                if not isinstance(conn, dict):
                    return json.dumps({
                        "success": False,
                        "message": "Invalid connection format",
                        "error": f"Connection at index {i} must be a dictionary with 'from' and 'to' keys"
                    }, indent=2)
                    
                if "from" not in conn or "to" not in conn:
                    return json.dumps({
                        "success": False,
                        "message": "Missing connection fields",
                        "error": f"Connection at index {i} must have both 'from' and 'to' fields"
                    }, indent=2)
            
            try:
                # 预处理连接数据：将字符串格式转换为字典格式
                if "connections" in netlist:
                    new_connections = []
                    for i, conn in enumerate(netlist["connections"]):
                        # 处理 "from" 字段
                        from_parts = []
                        if "from" in conn and isinstance(conn["from"], str):
                            # 检查是否有逗号分隔的多个引脚
                            if "," in conn["from"]:
                                # 有多个引脚，需要拆分为多个连接
                                from_pins = [pin.strip() for pin in conn["from"].split(",")]
                                for pin in from_pins:
                                    if "." in pin:
                                        comp, pin_id = pin.split(".", 1)
                                        from_parts.append({"component": comp, "pin": pin_id})
                                    else:
                                        # 无引脚标识，使用整个字符串作为组件名，引脚默认为"1"
                                        from_parts.append({"component": pin, "pin": "1"})
                            elif "." in conn["from"]:
                                # 单个引脚，标准格式
                                comp, pin = conn["from"].split(".", 1)
                                from_parts = [{"component": comp, "pin": pin}]
                            else:
                                # 无引脚标识，使用原始字符串
                                from_parts = [{"component": conn["from"], "pin": "1"}]
                        elif isinstance(conn.get("from"), dict):
                            # 已经是字典格式
                            if "component" in conn["from"] and "pin" in conn["from"]:
                                from_parts = [conn["from"]]
                            else:
                                return json.dumps({
                                    "success": False,
                                    "message": "Invalid connection format",
                                    "error": f"Connection 'from' at index {i} has invalid dictionary format, must contain 'component' and 'pin' fields"
                                }, indent=2)
                        else:
                            return json.dumps({
                                "success": False,
                                "message": "Invalid connection format",
                                "error": f"Connection 'from' at index {i} must be either a string or dictionary"
                            }, indent=2)
                        
                        # 处理 "to" 字段
                        to_parts = []
                        if "to" in conn and isinstance(conn["to"], str):
                            # 检查是否有逗号分隔的多个引脚
                            if "," in conn["to"]:
                                # 有多个引脚，需要拆分为多个连接
                                to_pins = [pin.strip() for pin in conn["to"].split(",")]
                                for pin in to_pins:
                                    if "." in pin:
                                        comp, pin_id = pin.split(".", 1)
                                        to_parts.append({"component": comp, "pin": pin_id})
                                    else:
                                        # 无引脚标识，使用整个字符串作为组件名，引脚默认为"1"
                                        to_parts.append({"component": pin, "pin": "1"})
                            elif "." in conn["to"]:
                                # 单个引脚，标准格式
                                comp, pin = conn["to"].split(".", 1)
                                to_parts = [{"component": comp, "pin": pin}]
                            else:
                                # 无引脚标识，使用原始字符串
                                to_parts = [{"component": conn["to"], "pin": "1"}]
                        elif isinstance(conn.get("to"), dict):
                            # 已经是字典格式
                            if "component" in conn["to"] and "pin" in conn["to"]:
                                to_parts = [conn["to"]]
                            else:
                                return json.dumps({
                                    "success": False,
                                    "message": "Invalid connection format",
                                    "error": f"Connection 'to' at index {i} has invalid dictionary format, must contain 'component' and 'pin' fields"
                                }, indent=2)
                        else:
                            return json.dumps({
                                "success": False,
                                "message": "Invalid connection format",
                                "error": f"Connection 'to' at index {i} must be either a string or dictionary"
                            }, indent=2)
                        
                        # 验证 from_parts 和 to_parts 是否为空
                        if not from_parts:
                            return json.dumps({
                                "success": False,
                                "message": "Invalid connection format",
                                "error": f"Could not parse 'from' field at connection index {i}"
                            }, indent=2)
                        
                        if not to_parts:
                            return json.dumps({
                                "success": False,
                                "message": "Invalid connection format",
                                "error": f"Could not parse 'to' field at connection index {i}"
                            }, indent=2)
                        
                        # 创建新的连接
                        # 处理一对多的情况
                        if len(from_parts) == 1 and len(to_parts) > 1:
                            # 一个源引脚连接到多个目标引脚
                            for to_part in to_parts:
                                new_connections.append({
                                    "from": from_parts[0],
                                    "to": to_part
                                })
                        elif len(to_parts) == 1 and len(from_parts) > 1:
                            # 多个源引脚连接到一个目标引脚
                            for from_part in from_parts:
                                new_connections.append({
                                    "from": from_part,
                                    "to": to_parts[0]
                                })
                        elif len(from_parts) == len(to_parts):
                            # 成对连接
                            for j in range(len(from_parts)):
                                new_connections.append({
                                    "from": from_parts[j],
                                    "to": to_parts[j]
                                })
                        else:
                            # 默认情况：创建所有可能的组合
                            for from_part in from_parts:
                                for to_part in to_parts:
                                    new_connections.append({
                                        "from": from_part,
                                        "to": to_part
                                    })
                    
                    # 用预处理后的连接替换原始连接
                    netlist["connections"] = new_connections
            
            except Exception as e:
                # 捕获连接预处理过程中的任何错误
                return json.dumps({
                    "success": False,
                    "message": "Error processing connections",
                    "error": f"Failed to process connections: {str(e)}"
                }, indent=2)
            
            # Generate a unique ID for this schematic
            schematic_id = f"schematic_{int(time.time())}"
            
            # Generate schematic based on available libraries
            schematic_info = {}
            
            try:
                # Try to generate a visual schematic using matplotlib
                schematic_info = self._generate_visual_schematic(netlist, schematic_id)
            except ImportError:
                print("Visualization libraries not available: No module named 'matplotlib'. Falling back to text-based schematic.")
                # Fall back to text-based schematic if matplotlib is not available
                schematic_info = self._generate_text_schematic(netlist, schematic_id)
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": "Error generating visual schematic",
                    "error": f"Failed to generate visual schematic: {str(e)}"
                }, indent=2)
            
            # Add a description of the schematic
            try:
                schematic_info["description"] = self._generate_schematic_description(netlist)
            except Exception as e:
                # If description generation fails, add a basic description
                schematic_info["description"] = "Circuit schematic (description generation failed)"
                print(f"Warning: Failed to generate schematic description: {str(e)}")
            
            # 构建标准化的输出结构
            if schematic_info.get("success", False):
                return json.dumps({
                    "success": True,
                    "message": f"Successfully generated schematic with ID {schematic_id}",
                    "data": schematic_info
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "message": "Failed to generate schematic",
                    "error": schematic_info.get("error", "Unknown error in schematic generation")
                }, indent=2)
            
        except Exception as e:
            error_msg = f"Error generating schematic: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return json.dumps({
                "success": False,
                "message": "Error generating schematic",
                "error": error_msg
            }, indent=2)
    
    def _generate_text_schematic(self, netlist, schematic_id):
        """Generate a text-based schematic representation"""
        components = netlist.get("components", [])
        connections = netlist.get("connections", [])
        
        # Create a text-based representation of the schematic
        schematic_text = "SCHEMATIC DIAGRAM (Text Representation)\n"
        schematic_text += "=" * 50 + "\n\n"
        
        # Component section
        schematic_text += "COMPONENTS:\n"
        schematic_text += "-" * 50 + "\n"
        for comp in components:
            comp_id = comp.get("id", "???")
            comp_type = comp.get("type", "Unknown")
            comp_value = comp.get("value", "")
            schematic_text += f"{comp_id}: {comp_type} {comp_value}\n"
        
        schematic_text += "\n"
        
        # Connection section
        schematic_text += "CONNECTIONS:\n"
        schematic_text += "-" * 50 + "\n"
        for conn in connections:
            # 获取连接的两端（预处理后应该都是字典格式）
            from_comp = conn.get("from", {}).get("component", "???")
            from_pin = conn.get("from", {}).get("pin", "???")
            to_comp = conn.get("to", {}).get("component", "???")
            to_pin = conn.get("to", {}).get("pin", "???")
            
            schematic_text += f"{from_comp}.{from_pin} --> {to_comp}.{to_pin}\n"
        
        # Save to file
        file_path = os.path.join(self.output_dir, f"{schematic_id}.txt")
        with open(file_path, 'w') as f:
            f.write(schematic_text)
        
        # Generate a basic ASCII art schematic
        ascii_schematic = self._generate_ascii_schematic(netlist)
        ascii_file_path = os.path.join(self.output_dir, f"{schematic_id}_ascii.txt")
        with open(ascii_file_path, 'w') as f:
            f.write(ascii_schematic)
        
        return {
            "success": True,
            "schematic_id": schematic_id,
            "file_path": file_path,
            "ascii_file_path": ascii_file_path,
            "schematic_type": "text",
            "note": "Text-based schematic generated (no visualization libraries available)"
        }
    
    def _generate_ascii_schematic(self, netlist):
        """Generate a simple ASCII art schematic"""
        components = netlist.get("components", [])
        connections = netlist.get("connections", [])
        
        # Create a grid
        grid_size = 40
        grid = [[' ' for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Place components on grid
        comp_positions = {}
        for i, comp in enumerate(components):
            comp_id = comp.get("id", f"C{i}")
            # Use provided position if available, otherwise place components linearly
            if "position" in comp and "x" in comp["position"] and "y" in comp["position"]:
                x = min(grid_size-1, max(0, int(comp["position"]["x"]) % grid_size))
                y = min(grid_size-1, max(0, int(comp["position"]["y"]) % grid_size))
            else:
                x = 5 + (i % 5) * 8
                y = 5 + (i // 5) * 8
            
            comp_positions[comp_id] = (x, y)
            
            # Place component ID on grid
            for j, char in enumerate(comp_id):
                if x + j < grid_size:
                    grid[y][x + j] = char
        
        # Draw connections
        for conn in connections:
            # 获取连接的组件名（预处理后应该都是字典格式）
            from_comp = conn.get("from", {}).get("component", "")
            to_comp = conn.get("to", {}).get("component", "")
            
            if from_comp in comp_positions and to_comp in comp_positions:
                x1, y1 = comp_positions[from_comp]
                x2, y2 = comp_positions[to_comp]
                
                # Draw a simple line (horizontal then vertical)
                # First horizontal
                start_x = min(x1, x2)
                end_x = max(x1, x2)
                mid_y = y1
                
                for x in range(start_x, end_x + 1):
                    if grid[mid_y][x] == ' ':
                        grid[mid_y][x] = '-'
                
                # Then vertical
                start_y = min(mid_y, y2)
                end_y = max(mid_y, y2)
                
                for y in range(start_y, end_y + 1):
                    if grid[y][end_x] == ' ':
                        grid[y][end_x] = '|'
                    elif grid[y][end_x] == '-':
                        grid[y][end_x] = '+'
        
        # Convert grid to string
        ascii_art = ""
        for row in grid:
            ascii_art += ''.join(row) + '\n'
        
        return ascii_art
    
    def _generate_visual_schematic(self, netlist, schematic_id):
        """Generate a visual schematic using matplotlib"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from matplotlib.patches import Rectangle, Circle, Arrow
            
            components = netlist.get("components", [])
            connections = netlist.get("connections", [])
            
            # Create figure
            fig, ax = plt.figure(figsize=(12, 8)), plt.gca()
            ax.set_xlim(0, 1000)
            ax.set_ylim(0, 1000)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Component shapes and colors by type
            comp_shapes = {
                "MICROCONTROLLER": {"shape": "rectangle", "width": 120, "height": 120, "color": "lightblue"},
                "MCU": {"shape": "rectangle", "width": 120, "height": 120, "color": "lightblue"},
                "SENSOR": {"shape": "rectangle", "width": 80, "height": 40, "color": "lightgreen"},
                "LED": {"shape": "circle", "radius": 20, "color": "yellow"},
                "RESISTOR": {"shape": "rectangle", "width": 60, "height": 20, "color": "beige"},
                "CAPACITOR": {"shape": "rectangle", "width": 40, "height": 20, "color": "lightgray"},
                "TRANSISTOR": {"shape": "circle", "radius": 25, "color": "lightcoral"},
                "SWITCH": {"shape": "rectangle", "width": 60, "height": 30, "color": "lightpink"},
                "default": {"shape": "rectangle", "width": 80, "height": 40, "color": "white"}
            }
            
            # Draw components
            comp_centers = {}
            for comp in components:
                comp_id = comp.get("id", "")
                comp_type = comp.get("type", "default").upper()
                comp_value = comp.get("value", "")
                
                # Get position or assign default
                if "position" in comp and "x" in comp["position"] and "y" in comp["position"]:
                    x = comp["position"]["x"]
                    y = comp["position"]["y"]
                else:
                    # Assign random position if not specified
                    x = np.random.randint(100, 900)
                    y = np.random.randint(100, 900)
                
                # Get component visual properties
                shape_info = comp_shapes.get(comp_type, comp_shapes["default"])
                
                # Draw component
                if shape_info["shape"] == "rectangle":
                    width, height = shape_info["width"], shape_info["height"]
                    rect = Rectangle((x-width/2, y-height/2), width, height, 
                                    facecolor=shape_info["color"], edgecolor='black', alpha=0.7)
                    ax.add_patch(rect)
                    comp_centers[comp_id] = (x, y)
                elif shape_info["shape"] == "circle":
                    radius = shape_info["radius"]
                    circle = Circle((x, y), radius, facecolor=shape_info["color"], 
                                    edgecolor='black', alpha=0.7)
                    ax.add_patch(circle)
                    comp_centers[comp_id] = (x, y)
                
                # Add component label
                label = f"{comp_id}\n{comp_value}" if comp_value else comp_id
                ax.text(x, y, label, ha='center', va='center', fontsize=9)
            
            # Draw connections
            for conn in connections:
                # 获取连接的两端（预处理后应该都是字典格式）
                from_comp = conn.get("from", {}).get("component", "")
                from_pin = conn.get("from", {}).get("pin", "")
                to_comp = conn.get("to", {}).get("component", "")
                to_pin = conn.get("to", {}).get("pin", "")
                
                if from_comp in comp_centers and to_comp in comp_centers:
                    x1, y1 = comp_centers[from_comp]
                    x2, y2 = comp_centers[to_comp]
                    
                    # Draw line
                    plt.plot([x1, x2], [y1, y2], 'k-', linewidth=1.5, alpha=0.6)
                    
                    # Add connection label (pin names) at midpoint
                    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                    conn_label = f"{from_pin} → {to_pin}"
                    ax.text(mid_x, mid_y, conn_label, fontsize=8, 
                            ha='center', va='center', 
                            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'))
            
            # Add title
            plt.title("Circuit Schematic")
            
            # Save schematic image
            png_path = os.path.join(self.output_dir, f"{schematic_id}.png")
            plt.savefig(png_path, dpi=150, bbox_inches='tight')
            
            # Save as SVG for vector graphics
            svg_path = os.path.join(self.output_dir, f"{schematic_id}.svg")
            plt.savefig(svg_path, format='svg', bbox_inches='tight')
            
            plt.close()
            
            return {
                "success": True,
                "schematic_id": schematic_id,
                "png_file_path": png_path,
                "svg_file_path": svg_path,
                "schematic_type": "visual"
            }
        except ImportError as e:
            # Fallback to text-based schematic if visualization libraries not available
            print(f"Visualization libraries not available: {str(e)}. Falling back to text-based schematic.")
            text_schematic = self._generate_text_schematic(netlist, schematic_id)
            text_schematic["note"] = "Matplotlib or numpy not available. Using text-based schematic instead."
            return text_schematic
        except Exception as e:
            # Handle other exceptions
            return {
                "success": False,
                "error": f"Error generating visual schematic: {str(e)}"
            }
    
    def _generate_schematic_description(self, netlist):
        """Generate a textual description of the schematic"""
        components = netlist.get("components", [])
        connections = netlist.get("connections", [])
        
        # Start building the description
        description = "This schematic includes the following components:\n"
        
        # List components
        for comp in components:
            comp_id = comp.get("id", "")
            comp_type = comp.get("type", "").upper()
            comp_value = comp.get("value", "")
            
            comp_str = f"- {comp_id} ({comp_type}"
            if comp_value:
                comp_str += f", {comp_value}"
            comp_str += ")"
            
            description += comp_str + "\n"
        
        # List connections
        description += "\nConnections:\n"
        for conn in connections:
            # 获取连接的两端
            from_comp = ""
            from_pin = ""
            to_comp = ""
            to_pin = ""
            
            # 处理 "from" 字段（已确保是字典格式）
            if "from" in conn:
                from_data = conn["from"]
                if isinstance(from_data, dict):
                    from_comp = from_data.get("component", "")
                    from_pin = from_data.get("pin", "")
            
            # 处理 "to" 字段（已确保是字典格式）
            if "to" in conn:
                to_data = conn["to"]
                if isinstance(to_data, dict):
                    to_comp = to_data.get("component", "")
                    to_pin = to_data.get("pin", "")
            
            description += f"- {from_comp}.{from_pin} connected to {to_comp}.{to_pin}\n"
        
        # Add a general description
        description += "\nCircuit description:\n"
        description += "This circuit represents a schematic design with the specified components and connections."
        
        return description
        
    # For compatibility with langchain newer versions
    def _run(self, input_str: str) -> str:
        return self._tool_run(input_str)


def generate_schematic(netlist: Dict) -> Dict:
    """Generate a schematic diagram for the given netlist.
    
    Args:
        netlist: Dictionary with components and connections.
        
    Returns:
        Dictionary with path to saved schematic file and description.
    """
    schematic_tool = SchematicTool()
    result_json = schematic_tool._tool_run(json.dumps(netlist))
    return json.loads(result_json)


if __name__ == "__main__":
    # Example usage
    test_netlist = {
        "components": [
            {"type": "MICROCONTROLLER", "id": "U1", "value": "AT89C51", "position": {"x": 100, "y": 100}},
            {"type": "SENSOR", "id": "U2", "value": "LM35", "position": {"x": 200, "y": 150}},
            {"type": "LED", "id": "D1", "value": "RED", "position": {"x": 300, "y": 100}},
            {"type": "RESISTOR", "id": "R1", "value": "220", "position": {"x": 300, "y": 200}}
        ],
        "connections": [
            {"from": {"component": "U1", "pin": "P1.0"}, "to": {"component": "D1", "pin": "Anode"}},
            {"from": {"component": "D1", "pin": "Cathode"}, "to": {"component": "R1", "pin": "Terminal1"}},
            {"from": {"component": "R1", "pin": "Terminal2"}, "to": {"component": "U1", "pin": "GND"}},
            {"from": {"component": "U2", "pin": "Vout"}, "to": {"component": "U1", "pin": "P1.5"}}
        ]
    }
    
    result = generate_schematic(test_netlist)
    print(json.dumps(result, indent=2)) 