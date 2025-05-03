#!/usr/bin/env python
"""
Script to parse Proteus simulation raw results into JSON format.
This is a simplified version for demonstration.
"""

import argparse
import json
import os
import sys
from datetime import datetime


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Parse Proteus simulation results")
    parser.add_argument("input_file", help="Path to input RAW results file")
    parser.add_argument("output_file", help="Path to output JSON file")
    return parser.parse_args()


def parse_raw_results(raw_file_path):
    """Parse Proteus RAW results file into a dictionary.
    
    This is a simplified version that generates mock data if the raw file doesn't exist.
    In a real implementation, this would parse the actual file format.
    
    Args:
        raw_file_path: Path to the Proteus RAW results file.
        
    Returns:
        Dictionary with parsed results.
    """
    # If the raw file doesn't exist, generate mock data for demonstration
    if not os.path.exists(raw_file_path):
        print(f"Warning: RAW file '{raw_file_path}' not found, generating mock data")
        return generate_mock_results()
    
    # In a real implementation, this would parse the actual file
    print(f"Parsing RAW file: {raw_file_path}")
    
    # Simplified mock parsing
    return generate_mock_results()


def generate_mock_results():
    """Generate mock simulation results for demonstration."""
    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "signals": {
            "LM35.Vout": {
                "node": "NODE1",
                "component": "LM35",
                "pin": "Vout",
                "values": [0.25, 0.251, 0.252, 0.253, 0.255]  # 25°C in volts (10mV/°C)
            },
            "LED1.Anode": {
                "node": "NODE2",
                "component": "LED1",
                "pin": "Anode",
                "values": [0.0, 0.0, 0.0, 0.0, 0.0]  # LED off at 25°C
            }
        },
        "logic_analyzer": {
            "channel_0": [0, 0, 0, 0, 0],  # LED state
            "channel_1": [0, 0, 0, 0, 0]   # Fan state
        },
        "uart_output": "Temperature: 25.0°C\nTemperature: 25.1°C\nTemperature: 25.2°C\nTemperature: 25.3°C\nTemperature: 25.5°C\n",
        "notes": [
            "Simulation ran for 5 seconds",
            "Temperature below 30°C threshold, LED and fan remain off"
        ]
    }


def write_json_results(results, output_file_path):
    """Write results dictionary to a JSON file."""
    try:
        with open(output_file_path, 'w') as f:
            json.dump(results, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing JSON file: {e}", file=sys.stderr)
        return False


def main():
    """Main function to parse Proteus simulation results."""
    args = parse_args()
    
    # Parse RAW results
    results = parse_raw_results(args.input_file)
    
    # Write to JSON file
    success = write_json_results(results, args.output_file)
    
    if success:
        print(f"Successfully wrote results to {args.output_file}")
        exit(0)
    else:
        print("Failed to write JSON results", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main() 