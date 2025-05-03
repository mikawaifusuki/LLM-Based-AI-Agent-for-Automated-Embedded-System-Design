import os
import subprocess
import tempfile
from typing import Dict, Optional, List, Union
import json

from langchain.tools import BaseTool

class CompilerTool(BaseTool):
    """Tool for compiling 8051 C code into HEX files using SDCC."""
    
    name = "CompilerTool"
    description = """
    Use this tool to compile 8051 C code into a HEX file.
    Input should be the C code as a string.
    Returns compilation result and path to the HEX file if successful.
    """
    
    output_dir: str = "backend/outputs"
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the compiler tool.
        
        Args:
            output_dir: Directory where compiled files will be stored.
        """
        super().__init__()
        if output_dir:
            self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _tool_run(self, c_code: str) -> str:
        """Run the compiler tool.
        
        Args:
            c_code: C code to compile.
            
        Returns:
            JSON string with compilation result.
        """
        try:
            # Create a temporary directory for compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write the C code to a file
                c_file_path = os.path.join(temp_dir, "main.c")
                with open(c_file_path, "w") as f:
                    f.write(c_code)
                
                # Set output file paths
                hex_file_name = "firmware.hex"
                temp_hex_path = os.path.join(temp_dir, hex_file_name)
                output_hex_path = os.path.join(self.output_dir, hex_file_name)
                
                # Compile the code using SDCC
                cmd = ["sdcc", "-mmcs51", c_file_path, "-o", temp_hex_path]
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise exception on non-zero exit
                )
                
                # Check if compilation was successful
                success = process.returncode == 0
                
                if success:
                    # Copy the compiled file to the output directory
                    with open(temp_hex_path, "rb") as src_file:
                        with open(output_hex_path, "wb") as dst_file:
                            dst_file.write(src_file.read())
                    
                    result = {
                        "success": True,
                        "hex_file": output_hex_path,
                        "stdout": process.stdout,
                        "stderr": process.stderr
                    }
                else:
                    # Compilation failed
                    result = {
                        "success": False,
                        "error": "Compilation failed",
                        "stdout": process.stdout,
                        "stderr": process.stderr
                    }
                
                return json.dumps(result, indent=2)
        
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error during compilation: {str(e)}"
            }, indent=2)
    
    # For compatibility with langchain newer versions
    def _run(self, c_code: str) -> str:
        return self._tool_run(c_code)


def compile_code(c_code: str) -> Dict:
    """Compile 8051 C code into a HEX file.
    
    Args:
        c_code: C code to compile.
        
    Returns:
        Dictionary with compilation result.
    """
    compiler_tool = CompilerTool()
    result_json = compiler_tool._tool_run(c_code)
    return json.loads(result_json)


if __name__ == "__main__":
    # Example usage
    code = """
    #include <8051.h>
    
    void delay(unsigned int ms) {
        unsigned int i, j;
        for (i = 0; i < ms; i++)
            for (j = 0; j < 120; j++);
    }
    
    void main() {
        P1_0 = 0;  // Set P1.0 as output for LED
        
        while (1) {
            P1_0 = !P1_0;  // Toggle LED
            delay(500);     // Delay for 500ms
        }
    }
    """
    
    result = compile_code(code)
    print(json.dumps(result, indent=2))
