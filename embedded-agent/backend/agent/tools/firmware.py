import os
import json
import time
import re
import traceback
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from langchain.tools.base import BaseTool

# 导入代码块组装器
from .code_assembler import CodeBlockLibrary, FirmwareAssembler
# 导入编译器工具和代码审查工具
from .compiler import CompilerTool
try:
    from .codereviewer import CodeReviewTool
    HAS_CODE_REVIEWER = True
except ImportError:
    HAS_CODE_REVIEWER = False

logger = logging.getLogger(__name__)

class TemplateLoader:
    """Template loader for firmware code generation."""
    
    def __init__(self, template_dir: str = "templates"):
        """Initialize template loader.
        
        Args:
            template_dir: Directory containing template files.
        """
        # Default to looking in templates directory relative to current file
        default_template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        
        self.template_dir = template_dir if os.path.exists(template_dir) else default_template_dir
        
        # Create template directory if it doesn't exist
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)
            self._create_default_templates()
    
    def load(self, template_name: str) -> str:
        """Load a template by name.
        
        Args:
            template_name: Name of the template file (without .c extension)
                
        Returns:
            Template content as string or empty string if template not found
        """
        template_path = os.path.join(self.template_dir, f"{template_name}.c")
        
        if not os.path.exists(template_path):
            print(f"Warning: Template '{template_name}' not found at {template_path}")
            return ""
            
        with open(template_path, "r") as f:
            return f.read()
    
    def _create_default_templates(self):
        """Create default templates if template directory is empty."""
        # Main template
        main_template = """/**
 * 8051 Microcontroller Firmware
 * Based on template: main_template.c
 */

#include <8051.h>
#include <stdio.h>
#include <stdlib.h>

// Configuration
#define CRYSTAL_FREQ <CRYSTAL_FREQ>  // Clock frequency in Hz

// Pin definitions
<PIN_DEFINITIONS>

// Function prototypes
void init_system(void);
void delay_ms(unsigned int ms);
<FUNCTION_PROTOTYPES>

/**
 * Main function
 */
void main(void) {
    // Initialize system
    init_system();
    
    <MAIN_INITIALIZATION>
    
    // Main loop
    while (1) {
        <MAIN_LOOP>
    }
}

/**
 * Initialize system
 */
void init_system(void) {
    <SYSTEM_INITIALIZATION>
}

/**
 * Delay function (milliseconds)
 */
void delay_ms(unsigned int ms) {
    unsigned int i, j;
    for (i = 0; i < ms; i++) {
        for (j = 0; j < 120; j++) {  // Adjust based on crystal frequency
            // NOP
        }
    }
}

<FUNCTION_IMPLEMENTATIONS>
"""
        
        # UART template
        uart_template = """/**
 * UART functions for 8051
 */

void init_uart(void) {
    SCON = 0x50;   // Mode 1 (8-bit UART), REN=1 (enable receiver)
    TMOD &= 0x0F;  // Clear Timer 1 bits
    TMOD |= 0x20;  // Timer 1 in Mode 2 (8-bit auto-reload)
    TH1 = 0xFD;    // Reload value for 9600 baud with 11.0592MHz crystal
    TR1 = 1;       // Start Timer 1
    TI = 1;        // Set TI to indicate ready to transmit
}

void uart_tx_char(char c) {
    SBUF = c;      // Load character into buffer
    while (!TI);   // Wait for transmission to complete
    TI = 0;        // Clear transmission flag
}

void uart_tx_string(char *str) {
    while (*str) {
        uart_tx_char(*str++);
    }
}
"""

        # Temperature sensor template
        temp_sensor_template = """/**
 * Temperature sensor functions for 8051
 */

unsigned int read_adc(unsigned char channel) {
    // Simulate ADC reading (Replace with actual ADC code)
    // For actual implementation, use the appropriate ADC interface
    // This is a placeholder
    return 512;  // Return mid-range value
}

float read_temperature(void) {
    unsigned int adc_value;
    float temperature;
    
    // Read ADC value from temperature sensor
    adc_value = read_adc(0);
    
    // Convert ADC value to temperature (LM35: 10mV per degree C)
    // For 10-bit ADC with 5V reference: 
    // temperature = (adc_value * 5.0 * 100.0) / 1024.0;
    temperature = (adc_value * 0.488);  // Simplified calculation
    
    return temperature;
}
"""

        # Fan control template
        fan_control_template = """/**
 * Fan control logic
 */
 
// Fan control based on temperature
if (temperature > <TEMP_THRESHOLD>) {
    // Temperature is high, turn on fan
    <FAN_PIN> = 1;
    <LED_PIN> = 1;  // Indicator LED on
    uart_tx_string("Fan ON\\r\\n");
} else {
    // Temperature is normal, turn off fan
    <FAN_PIN> = 0;
    <LED_PIN> = 0;  // Indicator LED off
    uart_tx_string("Fan OFF\\r\\n");
}
"""

        # LED blink template
        led_blink_template = """/**
 * LED blink logic
 */
 
// Toggle LED
<LED_PIN> = !<LED_PIN>;
        
// Delay
delay_ms(<BLINK_DELAY>);
"""

        # Temperature monitor main loop template
        temp_monitor_template = """/**
 * Temperature monitoring main loop
 */
 
// Variables
float temperature;
char temp_str[16];

// Read temperature
temperature = read_temperature();

// Convert temperature to string
sprintf(temp_str, "Temp: %.1f C\\r\\n", temperature);

// Send temperature via UART
uart_tx_string(temp_str);

<FAN_CONTROL>

// Delay before next reading
delay_ms(<LOOP_DELAY>);
"""

        # Create default templates
        templates = {
            "main_template": main_template,
            "uart_template": uart_template,
            "temp_sensor_template": temp_sensor_template,
            "fan_control_template": fan_control_template,
            "led_blink_template": led_blink_template,
            "temp_monitor_template": temp_monitor_template
        }
        
        for name, content in templates.items():
            with open(os.path.join(self.template_dir, f"{name}.c"), "w") as f:
                f.write(content)
                
        print(f"Created default templates in {self.template_dir}")

class FirmwareTool(BaseTool):
    """用于生成8051单片机固件代码的工具"""
    
    name: str = "FirmwareTool"
    description: str = """
    生成适用于8051单片机的C语言固件代码。
    接受一个包含以下内容的JSON格式设计规范：
    - mcu: 微控制器配置(型号、时钟频率等)
    - components: 组件列表(LED、传感器、执行器等)
    - functionality: 系统功能描述
    
    返回生成的C代码和其保存路径。
    """
    output_dir: str = "backend/outputs"
    max_fix_attempts: int = 3  # 最大修复尝试次数
    
    def __init__(
        self, 
        ai_service=None, 
        code_validator=None, 
        output_dir: str = None
    ):
        """初始化固件工具
        
        Args:
            ai_service: AI服务实例
            code_validator: 代码验证器实例
            output_dir: 输出目录，如果提供则覆盖默认值
        """
        super().__init__()
        
        # 如果提供了自定义输出目录，则使用它
        if output_dir:
            self.output_dir = output_dir
            
        # 存储AI服务和代码验证器
        self._ai_service = ai_service
        self._code_validator = code_validator
        
        # 初始化编译器和代码审查工具
        self._compiler = CompilerTool(output_dir=self.output_dir)
        if HAS_CODE_REVIEWER:
            self._code_reviewer = CodeReviewTool()
            logger.info("代码审查工具已初始化")
        else:
            self._code_reviewer = None
            logger.info("代码审查工具不可用")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"固件工具已初始化，输出目录: {self.output_dir}")
        
        # 记录AI服务和代码验证器状态
        logger.info(f"AI服务状态: {'可用' if ai_service else '不可用'}")
        logger.info(f"代码验证器状态: {'可用' if code_validator else '不可用'}")
        
    def _tool_run(self, input_str: str) -> str:
        """执行工具功能
        
        Args:
            input_str: 输入字符串，应为JSON格式的设计规范
            
        Returns:
            生成的代码和保存路径
        """
        try:
            # 解析输入JSON
            design = json.loads(input_str)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 确定文件名前缀
            prefix = "firmware"
            if "functionality" in design and isinstance(design["functionality"], dict):
                func_type = design["functionality"].get("main_task", "").lower()
                prefix_map = {
                    "temperature_monitoring": "temp_monitor",
                    "led_control": "led_control",
                    "fan_control": "fan_ctrl",
                    "motor_control": "motor_ctrl",
                    "data_logging": "data_logger"
                }
                prefix = prefix_map.get(func_type, "firmware")
            
            # 生成C代码文件路径
            output_filename = f"{prefix}_{timestamp}.c"
            main_c_path = os.path.join(self.output_dir, "main.c")
            dated_c_path = os.path.join(self.output_dir, output_filename)
            
            # 生成代码
            code = self._generate_8051_code(design)
            
            # 保存代码到文件
            with open(main_c_path, 'w') as f:
                f.write(code)
            
            # 同时保存一个带时间戳的副本
            with open(dated_c_path, 'w') as f:
                f.write(code)
                
            logger.info(f"固件代码已生成并保存到: {main_c_path}")
            
            # 尝试编译并处理可能的错误
            compilation_status = self._compile_and_fix_if_needed(code, design)
            
            # 构建响应
            response = {
                "message": "代码生成成功",
                "code_path": main_c_path,
                "archived_path": dated_c_path,
                "code_size": len(code),
                "preview": code[:150] + "..." if len(code) > 150 else code,
                "compilation": compilation_status
            }
            
            return json.dumps(response, ensure_ascii=False)
            
        except json.JSONDecodeError as e:
            error_msg = f"输入格式错误: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
            
        except Exception as e:
            error_msg = f"代码生成失败: {str(e)}"
            logger.error(error_msg)
            traceback.print_exc()
            return json.dumps({"error": error_msg})
            
    def _parse_sdcc_stderr(self, stderr_str: str) -> List[Dict[str, str]]:
        """解析SDCC的stderr输出，提取结构化的错误和警告信息"""
        parsed_errors = []
        # SDCC错误/警告格式通常是: filename:line: type: message
        # 例如: main.c:53: error 1: Undefined identifier 'P1_0'
        #       main.c:60: warning 117: Old style declaration
        pattern = re.compile(r"^(.*?):(\d+):\s*(error|warning)\s*\d*:\s*(.*)", re.MULTILINE)
        
        if not stderr_str:
            return []
            
        for match in pattern.finditer(stderr_str):
            parsed_errors.append({
                "file": match.group(1).strip(),
                "line": match.group(2).strip(),
                "type": match.group(3).strip(),
                "message": match.group(4).strip()
            })
            
        # 如果没有匹配到标准格式，尝试返回原始stderr的前几行作为基本错误信息
        if not parsed_errors and stderr_str.strip(): # Ensure stderr_str is not just whitespace
             lines = stderr_str.strip().split('\n')
             # Limit to first 5 lines or fewer
             summary_lines = lines[:5]
             raw_summary = "\n".join(summary_lines)
             if len(lines) > 5:
                 raw_summary += "\n... (more lines)"
             # Return a single entry representing the raw summary
             parsed_errors.append({
                 "file": "unknown",
                 "line": "unknown",
                 "type": "error",
                 "message": f"无法解析详细错误，原始输出摘要:\n{raw_summary}"
             })
                 
        return parsed_errors

    def _compile_and_fix_if_needed(self, code: str, design: Dict) -> Dict:
        """编译代码，如果有错误则尝试修复
        
        Args:
            code: 要编译的代码
            design: 设计规范，用于重新生成代码
            
        Returns:
            编译状态和结果信息
        """
        # 第一次尝试编译
        logger.info("尝试编译生成的代码...")
        compile_result_str = self._compiler._tool_run(code)
        compile_result = json.loads(compile_result_str)
        
        if compile_result.get("success", False):
            logger.info("编译成功!")
            return {
                "success": True,
                "message": "编译成功",
                "hex_file": compile_result.get("data", {}).get("hex_file_path", "")
            }
        
        # 编译失败，尝试修复
        attempt = 0
        current_code = code
        while attempt < self.max_fix_attempts:
            attempt += 1
            logger.info(f"编译失败，尝试修复 (尝试 {attempt}/{self.max_fix_attempts})...")
            
            # 获取并解析错误信息
            error_details = compile_result.get("error", {})
            error_message = error_details.get("message", "未知编译错误") # Keep the summary message
            stderr_output = error_details.get("details", {}).get("stderr", "")
            parsed_errors = self._parse_sdcc_stderr(stderr_output)
            
            if not parsed_errors:
                 # Fallback if parsing fails, use the summary message
                 logger.warning("无法从stderr解析结构化错误，将使用摘要信息")
                 parsed_errors = [{
                     "file": "unknown", 
                     "line": "unknown", 
                     "type": "error", 
                     "message": error_message
                 }]
            
            logger.info(f"解析到 {len(parsed_errors)} 个错误/警告")
            for err in parsed_errors:
                # Use dictionary access with get for safety
                err_type = err.get('type', 'unknown')
                err_file = err.get('file', 'unknown')
                err_line = err.get('line', 'unknown')
                err_msg = err.get('message', 'unknown')
                logger.debug(f"  - {err_type} in {err_file}:{err_line}: {err_msg}")

            # 使用代码审查工具获取修复建议
            review_suggestions = self._get_code_review(current_code, parsed_errors)
            
            # 使用AI修复代码
            if self._ai_service and self._ai_service.is_available():
                logger.info("使用AI服务修复代码...")
                fixed_code = self._fix_code_with_ai(current_code, parsed_errors, review_suggestions)
                
                if fixed_code:
                    current_code = fixed_code
                    
                    # 保存修复后的代码
                    fixed_path = os.path.join(self.output_dir, f"fixed_firmware_{attempt}.c")
                    with open(fixed_path, 'w') as f:
                        f.write(current_code)
                    logger.info(f"修复后的代码已保存到: {fixed_path}")
                    
                    # 再次尝试编译
                    logger.info(f"使用修复后的代码尝试编译...")
                    compile_result_str = self._compiler._tool_run(current_code)
                    compile_result = json.loads(compile_result_str)
                    
                    if compile_result.get("success", False):
                        logger.info(f"修复成功! 代码已成功编译。")
                        return {
                            "success": True,
                            "message": f"在第{attempt}次尝试后修复并编译成功",
                            "hex_file": compile_result.get("data", {}).get("hex_file_path", ""),
                            "fixed_code_path": fixed_path
                        }
                    # If compilation still fails, the loop continues with the new compile_result
                else:
                    logger.warning("AI未能生成修复代码，将结束修复尝试")
                    break # Exit loop if AI fails to produce any code
            else:
                logger.warning("AI服务不可用或AI修复失败，无法智能修复代码，结束修复尝试")
                break # Exit loop if AI is not available or fails
        
        # 所有尝试都失败或提前退出
        final_error_message = compile_result.get("error", {}).get("message", "未知编译错误")
        return {
            "success": False,
            "message": f"尝试修复{attempt}次后仍然编译失败",
            "error": final_error_message,
            "details": compile_result.get("error", {}).get("details", {})
        }
            
    def _get_code_review(self, code: str, parsed_errors: List[Dict]) -> str:
        """使用代码审查工具对代码进行审查
        
        Args:
            code: 要审查的代码
            parsed_errors: 解析后的结构化错误列表
            
        Returns:
            审查结果和修复建议
        """
        if not self._code_reviewer:
            error_summary = "\n".join([f"- {e.get('type','err')} at {e.get('file','?')}:{e.get('line','?')}: {e.get('message','?')}" for e in parsed_errors])
            return f"编译错误摘要:\n{error_summary}\n建议: 请检查代码语法和逻辑。"
        
        try:
            logger.info("使用代码审查工具分析代码...")
            # 格式化错误信息以包含在代码审查的上下文中
            error_context = "/*\n编译错误/警告详情:\n"
            for err in parsed_errors:
                 # Use dictionary access with get for safety
                err_type = err.get('type', 'unknown')
                err_file = err.get('file', 'unknown')
                err_line = err.get('line', 'unknown')
                err_msg = err.get('message', 'unknown')
                error_context += f"- {err_type} ({err_file}:{err_line}): {err_msg}\n"
            error_context += "*/\n\n"
            
            review_code = error_context + code
            review_result = self._code_reviewer._tool_run(review_code)
            logger.info("代码审查完成")
            return review_result
        except Exception as e:
            logger.error(f"代码审查失败: {str(e)}")
            error_summary = "\n".join([f"- {e.get('type','err')} at {e.get('file','?')}:{e.get('line','?')}: {e.get('message','?')}" for e in parsed_errors])
            return f"编译错误摘要:\n{error_summary}\n建议: 代码审查工具异常，请检查基本语法。"
    
    def _fix_code_with_ai(self, code: str, parsed_errors: List[Dict], review_suggestions: str) -> Optional[str]:
        """使用AI服务修复代码
        
        Args:
            code: 要修复的代码
            parsed_errors: 解析后的结构化错误列表
            review_suggestions: 代码审查建议
            
        Returns:
            修复后的代码，如果修复失败则返回None
        """
        if not self._ai_service or not self._ai_service.is_available():
            logger.warning("AI服务不可用，无法修复代码")
            return None
            
        try:
            # 格式化错误信息
            error_details_str = "\n".join([f"- {e.get('type','err')} ({e.get('file','?')}:{e.get('line','?')}): {e.get('message','?')}" for e in parsed_errors])
            
            prompt = f"""你是一个8051单片机固件专家。请修复以下C代码中的问题：

编译错误/警告详情:
{error_details_str}

代码审查建议:
{review_suggestions}

存在问题的代码:
```c
{code}
```

请仔细分析错误、警告和审查建议，修复所有问题，并确保代码能够使用SDCC编译器正确编译。返回完整的、修复后的C代码。不要添加任何解释、注释或markdown标记 (```)。只返回纯代码。
"""
            
            # 获取修复后的代码
            fixed_code = self._ai_service.complete_prompt(prompt)
            
            # 简单清理，以防万一AI还是加了标记
            fixed_code = fixed_code.strip()
            if fixed_code.startswith("```c"):
                fixed_code = fixed_code[len("```c"):].lstrip()
            if fixed_code.startswith("```"):
                 fixed_code = fixed_code[len("```"):].lstrip()
            if fixed_code.endswith("```"):
                fixed_code = fixed_code[:-len("```")].rstrip()
                
            # 检查返回的是否是看起来像代码的东西 (基本的健全性检查)
            if not fixed_code or "#include" not in fixed_code:
                 logger.warning("AI返回的修复结果似乎不是有效的C代码，修复失败")
                 return None

            logger.info("AI代码修复尝试完成")
            return fixed_code
            
        except Exception as e:
            logger.error(f"使用AI修复代码时发生异常: {str(e)}")
            return None
            
    def _generate_8051_code(self, design_dict):
        """生成8051单片机固件代码
        
        优先尝试使用AI组装器，如果失败或不可用，则回退到基本组装器。
        
        Args:
            design_dict: 设计规范
            
        Returns:
            生成的代码
        """
        # 提取设计参数
        mcu = design_dict.get('mcu', {})
        components = design_dict.get('components', [])
        functionality = design_dict.get('functionality', {})
        clock_freq = mcu.get('clock_freq', 12000000)
        
        code = None
        try:
            # 创建代码组装器
            code_assembler = FirmwareAssembler(
                ai_service=self._ai_service,
                code_validator=self._code_validator
            )
            
            # 优先尝试AI组装
            if code_assembler.ai_assembler:
                logger.info("尝试使用AI组装器生成初始代码...")
                code = code_assembler.assemble_firmware(components, functionality)
                if code:
                    logger.info("AI组装器成功生成初始代码")
                else:
                    logger.warning("AI组装器未能生成代码，回退到基本组装器...")
            
            # 如果AI组装失败或不可用，使用基本组装
            if not code:
                logger.info("使用基本代码块组装器生成代码...")
                code = code_assembler._basic_assemble_firmware(components, functionality)
                if not code:
                    logger.error("基本代码块组装器也未能生成代码")
                    # Return fallback code if even basic assembly fails
                    return self._generate_fallback_code()
            
            # 替换时钟频率
            if code:
                code = code.replace('CRYSTAL_FREQ 12000000', f'CRYSTAL_FREQ {clock_freq}')
            else:
                logger.error("无法生成任何代码，返回回退代码")
                return self._generate_fallback_code()

            # 验证生成的代码质量 (可选，但建议保留)
            if self._code_validator and code:
                validation_result = self._code_validator.validate(code)
                if not validation_result['success']:
                    issue_list = validation_result.get('issues', [])
                    logger.warning(f"初始生成的代码存在验证警告: {issue_list}")
                
            # 最后进行基本的编译准备
            if code:
                code = self._prepare_for_compilation(code)
                return code
            else:
                # This case should theoretically not be reached due to earlier checks
                logger.error("代码生成过程在最后准备阶段失败，返回回退代码")
                return self._generate_fallback_code()
            
        except Exception as e:
            logger.error(f"代码生成过程中发生严重错误: {str(e)}")
            traceback.print_exc()
            # 在失败时返回一个简单的有效代码
            return self._generate_fallback_code()
        
    def _prepare_for_compilation(self, code):
        """准备代码以便编译，移除不兼容内容"""
        # 移除可能的markdown格式
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines)
            
        # 确保代码以#include开始
        if not code.strip().startswith("#include"):
            code = f"#include <8051.h>\n\n{code}"
            
        # 确保代码包含main函数
        if "void main" not in code and "int main" not in code:
            logger.warning("代码缺少main函数，添加基本框架")
            code += """
void main(void) {
    // Initialize
    P1 = 0x00;
    
    // Main loop
    while(1) {
        // Your code here
        P1_0 = !P1_0;
        delay_ms(500);
    }
}

// Basic delay function
void delay_ms(unsigned int ms) {
    unsigned int i, j;
    for(i = 0; i < ms; i++)
        for(j = 0; j < 120; j++);
}
"""

        return code
        
    def _generate_fallback_code(self):
        """生成一个基本的回退代码，确保能编译通过"""
        return """
#include <8051.h>

// 基本的LED闪烁程序 - 回退代码
#define LED P1_0
#define DELAY_COUNT 30000

void delay(unsigned int count);

void main(void) {
    // 初始化
    P1 = 0x00;
    
    // 主循环
    while(1) {
        LED = !LED;
        delay(DELAY_COUNT);
    }
}

void delay(unsigned int count) {
    unsigned int i;
    for(i = 0; i < count; i++);
}
"""
    
    def _generate_pic_firmware(self, design, firmware_id):
        """Generate firmware for PIC microcontrollers - placeholder implementation"""
        # This is a placeholder for future implementation
        # Currently returns a simple message about the unimplemented feature
        
        # Determine filename prefix
        prefix = "pic_firmware"
        
        # Generate filename using versioned naming pattern
        c_filename = self._generate_versioned_filename(prefix, "c")
        
        return {
            "success": False,
            "error": "PIC firmware generation not yet implemented",
            "firmware_id": c_filename.replace(".c", "")
        }
    
    def _generate_avr_firmware(self, design, firmware_id):
        """Generate firmware for AVR microcontrollers - placeholder implementation"""
        # This is a placeholder for future implementation
        
        # Determine filename prefix
        prefix = "avr_firmware"
        
        # Generate filename using versioned naming pattern
        c_filename = self._generate_versioned_filename(prefix, "c")
        
        return {
            "success": False,
            "error": "AVR firmware generation not yet implemented",
            "firmware_id": c_filename.replace(".c", "")
        }
    
    def _generate_stm32_firmware(self, design, firmware_id):
        """Generate firmware for STM32 microcontrollers - placeholder implementation"""
        # This is a placeholder for future implementation
        
        # Determine filename prefix
        prefix = "stm32_firmware"
        
        # Generate filename using versioned naming pattern
        c_filename = self._generate_versioned_filename(prefix, "c")
        
        return {
            "success": False,
            "error": "STM32 firmware generation not yet implemented",
            "firmware_id": c_filename.replace(".c", "")
        }
    
    def _generate_esp_firmware(self, design, firmware_id):
        """Generate firmware for ESP microcontrollers - placeholder implementation"""
        # This is a placeholder for future implementation
        
        # Determine filename prefix
        prefix = "esp_firmware"
        
        # Generate filename using versioned naming pattern
        c_filename = self._generate_versioned_filename(prefix, "c")
        
        return {
            "success": False,
            "error": "ESP firmware generation not yet implemented",
            "firmware_id": c_filename.replace(".c", "")
        }
    
    def _generate_readme(self, design, mcu, firmware_id):
        """Generate a README file with firmware information"""
        mcu_type = mcu.get("type", "Unknown")
        functionality = design.get("functionality", {})
        description = functionality.get("description", "No description provided")
        
        readme = f"""# Firmware Documentation: {firmware_id}

## MCU Information
- Type: {mcu_type}
- Clock Frequency: {mcu.get("clock_frequency", "Unknown")} Hz

## System Description
{description}

## Components
"""
        # Add component information
        components = design.get("components", [])
        for comp in components:
            comp_type = comp.get("type", "Unknown")
            comp_id = comp.get("id", "")
            conn = comp.get("connected_to", "Unknown")
            readme += f"- {comp_type} ({comp_id}) connected to {conn}\n"
        
        readme += """
## Build Instructions
1. Compile the C file using an appropriate compiler for your microcontroller
   - For 8051: Use SDCC (Small Device C Compiler)
   - Example: `sdcc -mmcs51 firmware.c`
2. Convert the resulting .ihx file to a binary or hex file as needed
   - Example: `packihx firmware.ihx > firmware.hex`
3. Program the microcontroller using a suitable programmer

## Notes
- This firmware is auto-generated and may need adjustments for specific hardware
- Adjust delay functions based on the actual crystal frequency used
- Modify ADC reading functions according to the actual ADC implementation
"""
        
        return readme
    
    def _generate_versioned_filename(self, prefix: str, extension: str) -> str:
        """
        Generate a filename with versioned naming pattern (prefix_NNN.extension).
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
    
    # For compatibility with langchain newer versions
    def _run(self, input_str: str) -> str:
        return self._tool_run(input_str)


def generate_firmware(design_requirements: Dict) -> Dict:
    """Generate firmware code for embedded systems.
    
    Args:
        design_requirements: Dictionary with design requirements.
        
    Returns:
        Dictionary with generated firmware code.
    """
    firmware_tool = FirmwareTool()
    result_json = firmware_tool._tool_run(json.dumps(design_requirements))
    return json.loads(result_json)


if __name__ == "__main__":
    # Example usage
    design = {
        "mcu": {
            "type": "AT89C51",
            "clock_frequency": 11059200
        },
        "components": [
            {"type": "LED", "id": "LED1", "connected_to": "P1.0", "function": "status_indicator"},
            {"type": "SENSOR", "id": "TEMP1", "model": "LM35", "connected_to": "P1.5", "function": "temperature_sensing"},
            {"type": "FAN", "id": "FAN1", "connected_to": "P1.1", "function": "cooling"}
        ],
        "functionality": {
            "description": "Temperature monitoring system that turns on a fan when temperature exceeds 30C",
            "tasks": [
                {"name": "read_temperature", "frequency": "1000ms"},
                {"name": "control_fan", "condition": "temperature > 30"}
            ]
        }
    }
    
    result = generate_firmware(design)
    print(json.dumps(result, indent=2)) 