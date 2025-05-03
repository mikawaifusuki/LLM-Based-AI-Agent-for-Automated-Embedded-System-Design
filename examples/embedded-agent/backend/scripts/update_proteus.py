#!/usr/bin/env python
"""
Script to update Proteus design files (.dsn) based on a netlist and firmware.
"""

import argparse
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update Proteus design files")
    parser.add_argument("--template", required=True, help="Path to template DSN file")
    parser.add_argument("--output", required=True, help="Path to output DSN file")
    parser.add_argument("--netlist", required=True, help="JSON string with netlist")
    parser.add_argument("--firmware", required=True, help="Path to firmware HEX file")
    return parser.parse_args()


def update_proteus_design(
    template_path: str, 
    output_path: str, 
    netlist: Dict[str, Any], 
    firmware_path: str
) -> bool:
    """Update a Proteus design file with components, connections, and firmware.
    
    Args:
        template_path: Path to the template DSN file.
        output_path: Path to write the updated DSN file.
        netlist: Dictionary with components and connections.
        firmware_path: Path to the firmware HEX file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Copy the template file to the output location
        shutil.copy2(template_path, output_path)
        
        # Read the DSN file as text (it's not pure XML)
        with open(output_path, 'r') as f:
            dsn_content = f.read()
        
        # 1. Update components section
        components = netlist.get("components", [])
        dsn_content = add_components_to_dsn(dsn_content, components)
        
        # 2. Update connections
        connections = netlist.get("connections", [])
        # If connections aren't explicitly defined, try to extract them from component connection properties
        if not connections:
            connections = extract_connections_from_components(components)
        dsn_content = add_connections_to_dsn(dsn_content, connections)
        
        # 3. Update firmware path
        dsn_content = update_firmware_path(dsn_content, firmware_path)
        
        # 4. Add virtual instruments (Logic Analyzer, UART Terminal)
        dsn_content = add_virtual_instruments(dsn_content)
        
        # Write the updated content back to the file
        with open(output_path, 'w') as f:
            f.write(dsn_content)
        
        return True
    
    except Exception as e:
        print(f"Error updating Proteus design: {e}")
        return False


def add_components_to_dsn(dsn_content: str, components: List[Dict[str, Any]]) -> str:
    """Add components to the DSN file.
    
    Args:
        dsn_content: Content of the DSN file.
        components: List of component definitions.
        
    Returns:
        Updated DSN content.
    """
    # Find the components section in the DSN file
    components_section_pattern = r'(CIRCUIT.*?ENDCIRCUIT)'
    match = re.search(components_section_pattern, dsn_content, re.DOTALL)
    
    if not match:
        print("Components section not found in DSN file")
        return dsn_content
    
    components_section = match.group(1)
    new_components_section = components_section
    
    # Add each component to the section
    for component in components:
        component_type = component.get("type", "")
        component_id = component.get("id", "")
        position = component.get("position", {"x": 0, "y": 0})
        value = component.get("value", "")
        
        # Generate component entry in Proteus format
        component_entry = generate_proteus_component_entry(
            component_type, component_id, position, value
        )
        
        if component_entry:
            # Add the component before the ENDCIRCUIT tag
            new_components_section = new_components_section.replace(
                "ENDCIRCUIT", 
                f"{component_entry}\nENDCIRCUIT"
            )
    
    # Replace the old components section with the new one
    dsn_content = dsn_content.replace(components_section, new_components_section)
    
    return dsn_content


def generate_proteus_component_entry(
    component_type: str, 
    component_id: str, 
    position: Dict[str, int], 
    value: str = ""
) -> str:
    """Generate a component entry in Proteus DSN format.
    
    Args:
        component_type: Type of the component (e.g., AT89C51, LED).
        component_id: Identifier for the component.
        position: X and Y coordinates.
        value: Component value (e.g., resistance value, crystal frequency).
        
    Returns:
        Component entry string for the DSN file.
    """
    # Component mapping to Proteus model names
    component_models = {
        "AT89C51": "AT89C51",
        "LED": "LED-RED",
        "Resistor": "RES",
        "Crystal": "CRYSTAL",
        "Capacitor": "CAP",
        "LM35": "LM35",
        "DC_Motor": "MOTOR",
        "L293D": "L293D",
        "ADC0804": "ADC0804"
    }
    
    model = component_models.get(component_type)
    if not model:
        print(f"Unknown component type: {component_type}")
        return ""
    
    x = position.get("x", 0)
    y = position.get("y", 0)
    
    # Generate a unique reference if ID is not provided
    ref = component_id or f"{component_type[0]}{1}"
    
    # Basic component entry template
    entry = f"""
COMPONENT {ref} {model}
SHEET 1 {x} {y}
PROP Ref {ref}"""
    
    # Add value property if provided
    if value:
        entry += f"\nPROP Value {value}"
    
    return entry


def extract_connections_from_components(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract connections from component connection properties.
    
    Args:
        components: List of component definitions.
        
    Returns:
        List of connections.
    """
    connections = []
    
    # Create a mapping of component IDs to their types
    component_types = {comp["id"]: comp["type"] for comp in components if "id" in comp}
    
    # Process each component's connections
    for component in components:
        if "connections" not in component or "id" not in component:
            continue
        
        component_id = component["id"]
        component_connections = component["connections"]
        
        for pin, target in component_connections.items():
            # Parse the target (format: "ComponentID.PinName")
            if "." in target:
                target_id, target_pin = target.split(".", 1)
                
                connections.append({
                    "from": {"component": component_id, "pin": pin},
                    "to": {"component": target_id, "pin": target_pin}
                })
    
    return connections


def add_connections_to_dsn(dsn_content: str, connections: List[Dict[str, Any]]) -> str:
    """Add connections to the DSN file.
    
    Args:
        dsn_content: Content of the DSN file.
        connections: List of connection definitions.
        
    Returns:
        Updated DSN content.
    """
    # Find the connections section in the DSN file
    connections_section_pattern = r'(WIRE.*?ENDWIRE)'
    match = re.search(connections_section_pattern, dsn_content, re.DOTALL)
    
    # If no connections section exists, create one before ENDCIRCUIT
    if not match:
        dsn_content = dsn_content.replace(
            "ENDCIRCUIT",
            "WIRE\nENDWIRE\nENDCIRCUIT"
        )
        
        # Search again for the newly created section
        match = re.search(connections_section_pattern, dsn_content, re.DOTALL)
        if not match:
            print("Failed to create connections section")
            return dsn_content
    
    connections_section = match.group(1)
    new_connections_section = connections_section.replace("ENDWIRE", "")
    
    # Add each connection to the section
    for connection in connections:
        from_comp = connection.get("from", {}).get("component", "")
        from_pin = connection.get("from", {}).get("pin", "")
        to_comp = connection.get("to", {}).get("component", "")
        to_pin = connection.get("to", {}).get("pin", "")
        
        if from_comp and from_pin and to_comp and to_pin:
            # Generate connection entry in Proteus format
            connection_entry = f"WIRE {from_comp} {from_pin} {to_comp} {to_pin}"
            new_connections_section += connection_entry + "\n"
    
    new_connections_section += "ENDWIRE"
    
    # Replace the old connections section with the new one
    dsn_content = dsn_content.replace(connections_section, new_connections_section)
    
    return dsn_content


def update_firmware_path(dsn_content: str, firmware_path: str) -> str:
    """Update the firmware path in the DSN file.
    
    Args:
        dsn_content: Content of the DSN file.
        firmware_path: Path to the firmware HEX file.
        
    Returns:
        Updated DSN content.
    """
    # Find the firmware section in the DSN file
    firmware_pattern = r'(HEXFILE.*?)(\n|$)'
    
    # If a firmware section exists, replace it
    if re.search(firmware_pattern, dsn_content):
        dsn_content = re.sub(
            firmware_pattern,
            f'HEXFILE "{os.path.abspath(firmware_path)}"\n',
            dsn_content
        )
    else:
        # Otherwise, add it before ENDCIRCUIT
        dsn_content = dsn_content.replace(
            "ENDCIRCUIT",
            f'HEXFILE "{os.path.abspath(firmware_path)}"\nENDCIRCUIT'
        )
    
    return dsn_content


def add_virtual_instruments(dsn_content: str) -> str:
    """Add virtual instruments (Logic Analyzer, UART Terminal) to the DSN file.
    
    Args:
        dsn_content: Content of the DSN file.
        
    Returns:
        Updated DSN content with virtual instruments.
    """
    # Add Logic Analyzer
    logic_analyzer = """
COMPONENT LA1 LOGICANALYSER
SHEET 1 800 300
PROP Channels 8
PROP DataSize 1024
PROP Trigger 0
PROP TimeBase 1us
"""
    
    # Add UART Terminal
    uart_terminal = """
COMPONENT TERM1 TERMINAL
SHEET 1 900 300
PROP BaudRate 9600
PROP DataBits 8
PROP StopBits 1
PROP Parity None
"""
    
    # Add the virtual instruments before ENDCIRCUIT
    dsn_content = dsn_content.replace(
        "ENDCIRCUIT",
        f"{logic_analyzer}\n{uart_terminal}\nENDCIRCUIT"
    )
    
    # Add connections for virtual instruments (UART to P3.0/P3.1, Logic Analyzer to relevant pins)
    uart_connections = """
WIRE TERM1 TX AT89C51 P3.0
WIRE TERM1 RX AT89C51 P3.1
"""
    
    logic_analyzer_connections = """
WIRE LA1 D0 AT89C51 P1.0
WIRE LA1 D1 AT89C51 P1.1
WIRE LA1 D2 AT89C51 P1.2
WIRE LA1 D3 AT89C51 P1.3
"""
    
    # Add the connections to the WIRE section
    wire_section_pattern = r'(WIRE.*?)ENDWIRE'
    if re.search(wire_section_pattern, dsn_content, re.DOTALL):
        dsn_content = re.sub(
            wire_section_pattern,
            f'\\1{uart_connections}\n{logic_analyzer_connections}\nENDWIRE',
            dsn_content,
            flags=re.DOTALL
        )
    
    return dsn_content


def main():
    """Main function to update Proteus design files."""
    args = parse_args()
    
    try:
        netlist = json.loads(args.netlist)
        
        success = update_proteus_design(
            args.template,
            args.output,
            netlist,
            args.firmware
        )
        
        if success:
            print(f"Successfully updated Proteus design at {args.output}")
            exit(0)
        else:
            print("Failed to update Proteus design")
            exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
