import os
import subprocess
import tempfile
import shutil
import glob
import time
from typing import Dict, Optional, List, Tuple
import json
import logging
import traceback

from langchain.tools.base import BaseTool

# Import error handler
try:
    from ..utils.error_handler import ErrorHandler, CompilationError, handle_errors
    from ..utils.clean_code import clean_code_for_sdcc
    HAS_ERROR_HANDLER = True
except ImportError:
    HAS_ERROR_HANDLER = False
    
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('embedded_agent.compiler')
    
class CompilerTool(BaseTool):
    """Tool for compiling 8051 C code into HEX files using SDCC."""

    name: str = "CompilerTool"
    description: str = """
    Use this tool to compile 8051 C code into a HEX file.
    Input should be the C code as a string.
    Returns compilation result and path to the HEX file if successful.
    """

    output_dir: str = "output"
    sdcc_available: bool = False

    def __init__(self, output_dir: Optional[str] = None):
        super().__init__()
        if output_dir:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.sdcc_available = self._check_sdcc_available()
        if not self.sdcc_available:
            logger.error("SDCC compiler not found. Please install SDCC to enable compilation.")
            print("ERROR: SDCC compiler not found. Please install SDCC to enable compilation.")

    def _check_sdcc_available(self) -> bool:
        try:
            result = subprocess.run(["sdcc", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"SDCC compiler found: {result.stdout.splitlines()[0]}")
                print(f"SDCC compiler found: {result.stdout.splitlines()[0]}")
                return True
            return False
        except FileNotFoundError:
            return False
    
    def _find_latest_c_file(self) -> str:
        """Find the most recently created C file in the output directory."""
        c_files = []
        for root, _, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith(".c"):
                    full_path = os.path.join(root, file)
                    c_files.append((full_path, os.path.getmtime(full_path)))
        
        # Sort by modification time (newest first)
        c_files.sort(key=lambda x: x[1], reverse=True)
        
        if c_files:
            # Return the most recently modified file
            return c_files[0][0]
        
        return ""
            
    def _normalize_code(self, c_code: str) -> str:
        """Normalize C code before compilation."""
        try:
            # Use the clean_code_for_sdcc function if available
            if 'clean_code_for_sdcc' in globals():
                logger.info("Using clean_code_for_sdcc function to normalize code")
                return clean_code_for_sdcc(c_code)
        except Exception as e:
            logger.warning(f"Error using clean_code_for_sdcc: {str(e)}")
        
        # Fallback to basic normalization if the function is not available
        # Remove any markdown code blocks
        c_code = c_code.replace('```c', '').replace('```', '')
        
        # Ensure proper line endings
        c_code = c_code.replace('\r\n', '\n')
        
        # Remove trailing whitespace
        c_code = '\n'.join(line.rstrip() for line in c_code.split('\n'))
        
        # Ensure there's a newline at the end of the file
        if not c_code.endswith('\n'):
            c_code += '\n'
            
        return c_code

    def _generate_versioned_filename(self, prefix: str, extension: str) -> str:
        """
        Generate a filename with versioned naming pattern (prefix_NNN.ext).
        Automatically increments the number to avoid overwriting existing files.
        
        Args:
            prefix: The function descriptor prefix for the filename
            extension: The file extension without the dot
            
        Returns:
            A filename string in the format prefix_NNN.extension
        """
        version_num = 1
        while True:
            filename = f"{prefix}_{version_num:03d}.{extension}"
            file_path = os.path.join(self.output_dir, filename)
            if not os.path.exists(file_path):
                break
            version_num += 1
        
        return filename

    @handle_errors if HAS_ERROR_HANDLER else lambda f: f  # Apply decorator only if available
    def _tool_run(self, c_code: str = "") -> str:
        """Compile C code for 8051 microcontroller using SDCC.
        
        Args:
            c_code: String containing 8051 C code to compile. If empty, will try to find 
                   the latest C file in the output directory.
            
        Returns:
            JSON string with compilation results and paths.
        """
        if not self.sdcc_available:
            error_msg = "SDCC compiler not found. Unable to compile code."
            logger.error(error_msg)
            
            if HAS_ERROR_HANDLER:
                raise CompilationError(error_msg)
            else:
                return json.dumps({
                    "success": False,
                    "message": "Compilation failed: SDCC not available",
                    "error": error_msg
                }, indent=2)

        # Determine source file path
        c_file_path = ""
        
        # If code is provided directly, save it to a timestamped file
        if c_code:
            # Clean and normalize the code
            logger.info("Normalizing C code for compilation")
            try:
                c_code = self._normalize_code(c_code)
                # Log the first 100 characters of the cleaned code
                logger.debug(f"Normalized code (first 100 chars): {c_code[:100]}...")
            except Exception as e:
                error_msg = f"Error normalizing code: {str(e)}"
                logger.error(error_msg)
                
                if HAS_ERROR_HANDLER:
                    raise CompilationError(error_msg)
                else:
                    return json.dumps({
                        "success": False,
                        "message": "Compilation preparation failed",
                        "error": error_msg
                    }, indent=2)

            # Generate timestamped filename for C file
            c_filename = self._generate_versioned_filename("firmware", "c")
            c_file_path = os.path.join(self.output_dir, c_filename)
            
            # Save C code to file
            with open(c_file_path, "w") as f:
                f.write(c_code)
            logger.info(f"Saved C code to {c_file_path}")
        else:
            # No code provided, look for the latest .c file
            logger.info("No code provided, searching for the latest C file")
            c_file_path = self._find_latest_c_file()
            
            if not c_file_path:
                error_msg = f"No C files found in {self.output_dir} directory"
                logger.error(error_msg)
                
                if HAS_ERROR_HANDLER:
                    raise CompilationError(error_msg, code=258)  # Use code 258 for file not found
                else:
                    return json.dumps({
                        "success": False,
                        "message": "Compilation failed: No source file found",
                        "error": error_msg,
                        "error_code": 258
                    }, indent=2)

        # Define output HEX file path - use versioned naming pattern
        base_prefix = os.path.splitext(os.path.basename(c_file_path))[0].split('_')[0]
        hex_filename = self._generate_versioned_filename(base_prefix, "hex")
        output_hex_path = os.path.join(self.output_dir, hex_filename)
        output_hex_abs_path = os.path.abspath(output_hex_path)
        
        # Also create a standard firmware.hex file that gets overwritten each time
        standard_hex_name = "firmware.hex"
        standard_hex_path = os.path.join(self.output_dir, standard_hex_name)
        standard_hex_abs_path = os.path.abspath(standard_hex_path)
        
        logger.info(f"Output paths:")
        logger.info(f"  - Timestamped HEX: {output_hex_path}")
        logger.info(f"  - Standard HEX: {standard_hex_path}")

        logger.info(f"Compiling {c_file_path} using SDCC...")
        try:
            compile_result = self._compile_with_sdcc(c_file_path, output_hex_path)
            
            if not compile_result.get("success", False):
                error_msg = compile_result.get("error", "Unknown compilation error")
                logger.error(f"Compilation failed: {error_msg}")
                logger.debug(f"SDCC stderr: {compile_result.get('stderr', 'No stderr output')}")
                
                # Handle file not found error (code 258)
                if "No such file or directory" in error_msg and c_code:
                    logger.warning("Source file not found. Retrying with saved code.")
                    
                    # Save the code again and retry
                    new_c_filename = self._generate_versioned_filename("firmware", "c")
                    new_c_file_path = os.path.join(self.output_dir, new_c_filename)
                    
                    with open(new_c_file_path, "w") as f:
                        f.write(c_code)
                    logger.info(f"Saved C code again to {new_c_file_path}")
                    
                    # Try compiling again
                    compile_result = self._compile_with_sdcc(new_c_file_path, output_hex_path)
                    
                    if not compile_result.get("success", False):
                        error_msg = compile_result.get("error", "Unknown compilation error after retry")
                        logger.error(f"Compilation retry failed: {error_msg}")
                        
                        if HAS_ERROR_HANDLER:
                            raise CompilationError(
                                error_msg, 
                                details={
                                    "stdout": compile_result.get("stdout", ""),
                                    "stderr": compile_result.get("stderr", "")
                                }
                            )
                        else:
                            return json.dumps({
                                "success": False,
                                "message": "Compilation retry failed",
                                "error": error_msg,
                                "data": {
                                    "stdout": compile_result.get("stdout", ""),
                                    "stderr": compile_result.get("stderr", "")
                                }
                            }, indent=2)
                else:
                    if HAS_ERROR_HANDLER:
                        raise CompilationError(
                            error_msg, 
                            details={
                                "stdout": compile_result.get("stdout", ""),
                                "stderr": compile_result.get("stderr", "")
                            }
                        )
                    else:
                        return json.dumps({
                            "success": False,
                            "message": "Compilation failed",
                            "error": error_msg,
                            "data": {
                                "stdout": compile_result.get("stdout", ""),
                                "stderr": compile_result.get("stderr", "")
                            }
                        }, indent=2)
            
            # If compilation successful, also copy to the standard firmware.hex path
            if os.path.exists(output_hex_abs_path):
                shutil.copy(output_hex_abs_path, standard_hex_abs_path)
                logger.info(f"Copied HEX file to standard path: {standard_hex_abs_path}")
            
            logger.info("Compilation successful")
            return json.dumps({
                "success": True,
                "message": "Compilation successful",
                "data": {
                    "c_file_path": c_file_path,
                    "hex_file_path": output_hex_abs_path,
                    "standard_hex_path": standard_hex_abs_path,
                    "stdout": compile_result.get("stdout", ""),
                    "stderr": compile_result.get("stderr", "")
                }
            }, indent=2)

        except Exception as e:
            error_msg = f"Compilation error: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            
            if HAS_ERROR_HANDLER:
                raise CompilationError(error_msg)
            else:
                return json.dumps({
                    "success": False,
                    "message": "Compilation error",
                    "error": error_msg
                }, indent=2)

    def _compile_with_sdcc(self, c_file_path: str, output_hex_path: str) -> Dict:
        """Compile C file using SDCC and generate HEX file."""
        # Get absolute paths
        c_file_abs_path = os.path.abspath(c_file_path)
        output_hex_abs_path = os.path.abspath(output_hex_path)
        
        logger.info(f"Compiling with absolute paths:")
        logger.info(f"  - Source file: {c_file_abs_path}")
        logger.info(f"  - Output HEX: {output_hex_abs_path}")
        
        # Check if source file exists
        if not os.path.exists(c_file_abs_path):
            error_msg = f"Source file not found: {c_file_abs_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": f"Error 258: Failed to open input file '{c_file_path}' (No such file or directory)"
            }
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_hex_abs_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Use the original directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = ["sdcc", "-mmcs51", c_file_abs_path]
            logger.debug(f"Running command: {' '.join(cmd)} in {temp_dir}")

            process = subprocess.run(
                cmd, cwd=temp_dir, capture_output=True, text=True
            )
            
            logger.debug(f"SDCC return code: {process.returncode}")
            logger.debug(f"SDCC stdout: {process.stdout}")
            logger.debug(f"SDCC stderr: {process.stderr}")

            if process.returncode == 0:
                base_name = os.path.splitext(os.path.basename(c_file_abs_path))[0]
                # Check for the IHX file in the current directory
                ihx_file = f"{base_name}.ihx"
                
                if os.path.exists(ihx_file):
                    # Generate HEX from IHX using packihx
                    logger.info(f"Found IHX file: {ihx_file}")
                    try:
                        packihx_process = subprocess.run(
                            ["packihx", ihx_file], 
                            capture_output=True, 
                            text=True
                        )
                        if packihx_process.returncode == 0:
                            # Write packihx output to the HEX file
                            with open(output_hex_abs_path, 'w') as f:
                                f.write(packihx_process.stdout)
                            logger.info(f"Generated HEX file at {output_hex_abs_path}")
                        else:
                            logger.error(f"packihx failed: {packihx_process.stderr}")
                            return {
                                "success": False,
                                "error": f"Failed to convert IHX to HEX: {packihx_process.stderr}",
                                "stdout": process.stdout,
                                "stderr": process.stderr
                            }
                    except Exception as e:
                        logger.error(f"Error running packihx: {str(e)}")
                        return {
                            "success": False,
                            "error": f"Error converting IHX to HEX: {str(e)}",
                            "stdout": process.stdout,
                            "stderr": process.stderr
                        }
                else:
                    # Check other locations for IHX/HEX files
                    ihx_files = glob.glob("*.ihx") + glob.glob(os.path.join(temp_dir, "*.ihx"))
                    hex_files = glob.glob("*.hex") + glob.glob(os.path.join(temp_dir, "*.hex"))
                    
                    all_hex_files = ihx_files + hex_files
                    
                    if all_hex_files:
                        # Found at least one HEX/IHX file
                        source_file = all_hex_files[0]
                        logger.info(f"Found alternative HEX/IHX file: {source_file}")
                        
                        if source_file.endswith('.ihx'):
                            # Convert IHX to HEX
                            try:
                                packihx_process = subprocess.run(
                                    ["packihx", source_file], 
                                    capture_output=True, 
                                    text=True
                                )
                                if packihx_process.returncode == 0:
                                    with open(output_hex_abs_path, 'w') as f:
                                        f.write(packihx_process.stdout)
                                    logger.info(f"Generated HEX file at {output_hex_abs_path}")
                                else:
                                    logger.error(f"packihx failed: {packihx_process.stderr}")
                                    return {
                                        "success": False,
                                        "error": f"Failed to convert IHX to HEX: {packihx_process.stderr}",
                                        "stdout": process.stdout,
                                        "stderr": process.stderr
                                    }
                            except Exception as e:
                                logger.error(f"Error running packihx: {str(e)}")
                                return {
                                    "success": False,
                                    "error": f"Error converting IHX to HEX: {str(e)}",
                                    "stdout": process.stdout,
                                    "stderr": process.stderr
                                }
                        else:
                            # Direct copy for HEX files
                            shutil.copy(source_file, output_hex_abs_path)
                            logger.info(f"Copied HEX file from {source_file} to {output_hex_abs_path}")
                    else:
                        logger.error("Compilation succeeded but no HEX/IHX file found")
                        return {
                            "success": False,
                            "error": "Compilation succeeded but no HEX/IHX file found",
                            "stdout": process.stdout,
                            "stderr": process.stderr
                        }

                return {
                    "success": True,
                    "hex_file": output_hex_abs_path,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }

            else:
                logger.error(f"Compilation failed with code {process.returncode}")
                # Include details about the error in the stderr
                error_lines = process.stderr.splitlines()
                error_summary = "\n".join(error_lines[:10])  # First 10 lines of errors
                if len(error_lines) > 10:
                    error_summary += f"\n... and {len(error_lines) - 10} more errors/warnings"
                
                return {
                    "success": False,
                    "error": f"Compilation failed: {error_summary}",
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }

    def _run(self, c_code: str = "") -> str:
        return self._tool_run(c_code)

@handle_errors if HAS_ERROR_HANDLER else lambda f: f  # Apply decorator only if available
def compile_code(c_code: str = "") -> Dict:
    """Compile 8051 C code into a HEX file."""
    compiler_tool = CompilerTool()
    result_json = compiler_tool._tool_run(c_code)
    return json.loads(result_json)


if __name__ == "__main__":
    # Test example
    code = """
    #include <reg51.h>

    void delay(unsigned int ms) {
        unsigned int i, j;
        for (i = 0; i < ms; i++)
            for (j = 0; j < 120; j++);
    }

    void main() {
        P1_0 = 0;
        while (1) {
            P1_0 = !P1_0;
            delay(500);
        }
    }
    """
    result = compile_code(code)
    print(json.dumps(result, indent=2))
