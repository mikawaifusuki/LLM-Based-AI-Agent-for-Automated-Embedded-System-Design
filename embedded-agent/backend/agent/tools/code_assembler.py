import os
import re
import json
import logging
from typing import Dict, List, Optional, Set, Any, Union

# 导入AI服务和代码验证器
try:
    from ..utils.ai_service import AIService
    from ..utils.code_validator import CodeValidator
    HAS_AI_SERVICE = True
except ImportError:
    HAS_AI_SERVICE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('embedded_agent.code_assembler')

class CodeBlockLibrary:
    """代码块库，用于加载和管理预定义的代码块"""
    
    def __init__(self, blocks_dir: str = None):
        """初始化代码块库
        
        Args:
            blocks_dir: 代码块目录，默认为模块同级目录下的templates
        """
        if blocks_dir is None:
            # 默认为模块同级目录下的templates
            blocks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
            
        self.blocks_dir = blocks_dir
        self.blocks = {}
        self.block_info = {}  # 存储代码块元数据
        self.loaded_blocks = set()
        
        # 加载代码块
        self._load_blocks()
        
    def _load_blocks(self):
        """加载所有代码块"""
        # 检查目录是否存在
        if not os.path.exists(self.blocks_dir):
            logger.warning(f"代码块目录不存在: {self.blocks_dir}")
            return
            
        # 遍历所有子目录
        for root, _, files in os.walk(self.blocks_dir):
            for file in files:
                if file.endswith('.c') or file.endswith('.h'):
                    # 构建代码块标识符
                    rel_path = os.path.relpath(root, self.blocks_dir)
                    if rel_path == '.':
                        block_id = file.rsplit('.', 1)[0]  # 去掉扩展名
                    else:
                        # 使用相对路径和文件名作为标识符
                        block_id = f"{rel_path.replace(os.path.sep, '/')}/{file.rsplit('.', 1)[0]}"
                    
                    # 将路径中的目录分隔符统一为/，便于后续处理
                    block_id = block_id.replace('\\', '/')
                    
                    # 加载代码块内容
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        self.blocks[block_id] = content
                        
                        # 提取代码块元数据
                        self.block_info[block_id] = {
                            "id": block_id,
                            "path": file_path,
                            "content": content,
                            "type": file.split('.')[-1],  # 文件类型（c或h）
                            "category": rel_path if rel_path != '.' else "root"
                        }
                        
        logger.info(f"已加载 {len(self.blocks)} 个代码块")
        
    def get_block(self, block_id: str) -> str:
        """获取指定ID的代码块
        
        Args:
            block_id: 代码块ID，形如 "base/base_frame" 或 "drivers/uart"
            
        Returns:
            代码块内容，如果不存在则返回空字符串
        """
        # 记录已加载的代码块
        self.loaded_blocks.add(block_id)
        
        # 尝试直接获取
        if block_id in self.blocks:
            return self.blocks[block_id]
            
        # 尝试添加前缀路径
        for prefix in ['base/', 'drivers/', 'logic/', 'main/']:
            prefixed_id = f"{prefix}{block_id}"
            if prefixed_id in self.blocks:
                self.loaded_blocks.add(prefixed_id)
                return self.blocks[prefixed_id]
                
        logger.warning(f"代码块不存在: {block_id}")
        return ""
        
    def get_block_info(self, block_id: str) -> Dict[str, Any]:
        """获取指定ID的代码块信息
        
        Args:
            block_id: 代码块ID
            
        Returns:
            代码块信息，如果不存在则返回空字典
        """
        if block_id in self.block_info:
            return self.block_info[block_id]
            
        # 尝试添加前缀路径
        for prefix in ['base/', 'drivers/', 'logic/', 'main/']:
            prefixed_id = f"{prefix}{block_id}"
            if prefixed_id in self.block_info:
                return self.block_info[prefixed_id]
                
        return {}
        
    def list_blocks(self) -> List[str]:
        """列出所有可用的代码块ID"""
        return list(self.blocks.keys())
        
    def get_loaded_blocks(self) -> Set[str]:
        """获取已加载的代码块集合"""
        return self.loaded_blocks
        
    def get_all_blocks_info(self) -> List[Dict[str, Any]]:
        """获取所有代码块的详细信息"""
        return list(self.block_info.values())


class AICodeAssembler:
    """使用AI服务组装固件代码的类"""
    
    def __init__(self, ai_service=None, code_block_library=None):
        """初始化AI代码组装器
        
        Args:
            ai_service: AI服务实例
            code_block_library: 代码块库实例，如果未提供则创建新的
        """
        self.ai_service = ai_service
        self.code_block_library = code_block_library or CodeBlockLibrary()
        self.logger = logging.getLogger(__name__)
        
        # 记录可用代码块
        self.available_blocks = self.code_block_library.list_blocks()
        self.logger.info(f"AI代码组装器初始化完成，可用代码块: {len(self.available_blocks)}")
    
    def assemble_firmware(self, components, functionality):
        """使用AI组装固件代码
        
        Args:
            components: 组件列表
            functionality: 功能描述
            
        Returns:
            生成的固件代码
        """
        if not self.ai_service or not self.ai_service.is_available():
            self.logger.warning("AI服务不可用，无法使用AI组装代码")
            return None
            
        try:
            # 准备要发送给AI的需求
            requirements = {
                "components": components,
                "functionality": functionality,
                "available_code_blocks": self.available_blocks
            }
            
            # 获取代码块的内容和描述
            block_contents = {}
            for block_id in self.available_blocks:
                content = self.code_block_library.get_block(block_id)
                if content:
                    purpose = self.ai_service._extract_purpose(content)
                    functions = self.ai_service._extract_functions(content)
                    block_contents[block_id] = {
                        "purpose": purpose,
                        "functions": functions
                    }
            
            # 添加代码块内容到需求
            requirements["block_details"] = block_contents
            
            # 生成代码组装计划
            self.logger.info("正在生成代码组装计划...")
            assembly_plan = self.ai_service.generate_code_assembly_plan(requirements)
            
            if not assembly_plan:
                self.logger.warning("无法生成代码组装计划，将使用AI直接生成代码")
                # 直接使用AI生成完整代码
                code = self.ai_service.generate_code({"components": components, "functionality": functionality})
                return code
            
            # 根据计划组装代码
            self.logger.info(f"使用AI生成的计划组装代码: {assembly_plan.get('blocks_to_use', [])}")
            
            # 将计划和需求传递给AI生成最终代码
            code_generation_input = {
                "components": components,
                "functionality": functionality,
                "assembly_plan": assembly_plan,
                "available_blocks": self.available_blocks
            }
            
            # 生成代码
            code = self.ai_service.generate_code(code_generation_input)
            self.logger.info(f"AI成功生成代码，大小: {len(code)} 字符")
            
            return code
            
        except Exception as e:
            self.logger.error(f"AI代码组装失败: {str(e)}")
            return None


class FirmwareAssembler:
    """固件代码组装器工厂类，根据可用条件选择适当的组装器"""
    
    def __init__(self, ai_service=None, code_validator=None):
        """初始化固件组装器
        
        Args:
            ai_service: AI服务实例，如果提供则尝试使用AI组装
            code_validator: 代码验证器实例
        """
        self.logger = logging.getLogger(__name__)
        self.code_block_library = CodeBlockLibrary()
        self.ai_service = ai_service
        self.code_validator = code_validator
        
        # 创建基本组装器和AI组装器
        if ai_service and hasattr(ai_service, 'is_available') and ai_service.is_available():
            self.logger.info("AI服务可用，将使用AI代码组装器")
            self.ai_assembler = AICodeAssembler(ai_service, self.code_block_library)
        else:
            self.logger.info("AI服务不可用，将仅使用基本代码组装器")
            self.ai_assembler = None
    
    def assemble_firmware(self, components, functionality):
        """组装固件代码
        
        Args:
            components: 组件列表
            functionality: 功能描述
            
        Returns:
            组装后的固件代码
        """
        # 先尝试使用AI组装
        if self.ai_assembler:
            self.logger.info("尝试使用AI组装代码...")
            code = self.ai_assembler.assemble_firmware(components, functionality)
            
            # 如果AI组装成功且通过验证，则返回结果
            if code and self.code_validator:
                validation_result = self.code_validator.validate(code)
                if validation_result['success']:
                    self.logger.info("AI组装代码验证通过")
                    return code
                else:
                    self.logger.warning(f"AI组装代码验证失败: {validation_result.get('issues', [])}")
                    # 尝试修复代码问题
                    if self.ai_service:
                        try:
                            self.logger.info("尝试修复代码问题...")
                            fixed_code = self.ai_service.fix_code_issues(code, validation_result.get('issues', []))
                            
                            # 再次验证
                            validation_result = self.code_validator.validate(fixed_code)
                            if validation_result['success']:
                                self.logger.info("修复后的代码验证通过")
                                return fixed_code
                        except Exception as e:
                            self.logger.error(f"修复代码问题失败: {str(e)}")
            
            if code:
                self.logger.info("使用AI组装的代码，但未进行验证")
                return code
        
        # 如果AI组装失败或不可用，使用基本组装
        self.logger.info("使用基本代码组装器...")
        return self._basic_assemble_firmware(components, functionality)
        
    def _basic_assemble_firmware(self, components, functionality):
        """使用基本方法组装固件代码
        
        Args:
            components: 组件列表
            functionality: 功能描述
            
        Returns:
            组装后的固件代码
        """
        self.logger.info("开始使用基本组装器组装代码")
        
        # 创建一个新的组装上下文
        self.loaded_blocks = set()
        
        # 1. 加载基础框架
        base_frame = self.code_block_library.get_block("base/base_frame")
        if not base_frame:
            self.logger.error("基础框架代码块未找到")
            return "// 错误: 基础框架代码块未找到\n"
            
        self.logger.info("已加载基础框架")
            
        # 2. 提取和分析组件类型
        has_temp_sensor = False
        has_led = False
        has_fan = False
        
        for component in components:
            comp_type = component.get("type", "").upper()
            
            if comp_type == "LED":
                has_led = True
            elif comp_type == "SENSOR" and "LM35" in component.get("model", "").upper():
                has_temp_sensor = True
            elif comp_type in ["FAN", "MOTOR"]:
                has_fan = True
                
        self.logger.info(f"组件分析: LED={has_led}, 温度传感器={has_temp_sensor}, 风扇={has_fan}")
                
        # 3. 根据组件组合选择合适的主循环代码块
        if has_temp_sensor and has_fan:
            self.logger.info("使用温度监控和风扇控制主循环")
            # 温度监控和风扇控制系统，使用完整的预定义代码块
            main_code = self.code_block_library.get_block("main/main_loop_temp_fan")
            if not main_code:
                self.logger.error("温度风扇控制代码块未找到")
                return "// 错误: 未找到温度风扇控制代码块\n"
                
            # 替换引脚定义
            for component in components:
                comp_type = component.get("type", "").upper()
                pin = component.get("connected_to", "")
                
                if comp_type == "LED":
                    main_code = main_code.replace("LED_PIN P1_0", f"LED_PIN {pin}")
                elif comp_type == "SENSOR" and "LM35" in component.get("model", "").upper():
                    main_code = main_code.replace("TEMP_SENSOR_PIN P1_5", f"TEMP_SENSOR_PIN {pin}")
                elif comp_type in ["FAN", "MOTOR"]:
                    main_code = main_code.replace("FAN_PIN P1_2", f"FAN_PIN {pin}")
                
            # 替换温度阈值
            threshold = 30.0  # 默认值
            if isinstance(functionality, dict) and "threshold" in functionality:
                threshold = functionality["threshold"]
            main_code = main_code.replace("TEMP_THRESHOLD 30.0", f"TEMP_THRESHOLD {threshold}")
            
            return main_code
            
        elif has_led and not has_temp_sensor and not has_fan:
            self.logger.info("使用LED闪烁主循环")
            # 简单LED闪烁系统，使用完整的预定义代码块
            main_code = self.code_block_library.get_block("main/main_loop_basic")
            if not main_code:
                self.logger.error("基本LED闪烁代码块未找到")
                return "// 错误: 未找到基本LED闪烁代码块\n"
                
            # 替换引脚定义
            for component in components:
                if component.get("type", "").upper() == "LED":
                    pin = component.get("connected_to", "P1_0")
                    main_code = main_code.replace("LED_PIN P1_0", f"LED_PIN {pin}")
                    
            return main_code
            
        else:
            self.logger.warning("没有找到匹配的预定义主循环代码块，将使用基础框架")
            # 如果没有找到匹配的预定义代码块，返回一个基本框架
            return """
#include <8051.h>

// 配置
#define CRYSTAL_FREQ 12000000

// 设备引脚定义
#define LED P1_0

// 函数原型
void delay_ms(unsigned int ms);

void main(void) {
    // 初始化
    P1 = 0x00;  // 所有P1端口置低
    
    // 主循环
    while (1) {
        // 基本LED闪烁
        LED = !LED;
        delay_ms(500);
    }
}

// 延时函数实现
void delay_ms(unsigned int ms) {
    unsigned int i, j;
    for(i = 0; i < ms; i++)
        for(j = 0; j < 120; j++);  // 大约1ms延时@12MHz
}
"""
    
    def _generate_pin_definitions(self, components):
        """生成引脚定义代码
        
        Args:
            components: 组件列表
            
        Returns:
            引脚定义代码
        """
        pin_defs = []
        
        for component in components:
            comp_type = component.get("type", "").upper()
            comp_id = component.get("id", "")
            connected_to = component.get("connected_to", "")
            
            if not connected_to:
                continue
                
            # 处理引脚定义格式
            pin_name = connected_to.replace(".", "_")
            
            if comp_type == "LED":
                pin_defs.append(f"#define {comp_id}_PIN {pin_name}  // {component.get('function', '')}")
            elif comp_type == "SENSOR" and "LM35" in component.get("model", "").upper():
                pin_defs.append(f"#define TEMP_SENSOR_PIN {pin_name}  // LM35")
            elif comp_type in ["FAN", "MOTOR"]:
                pin_defs.append(f"#define {comp_id}_PIN {pin_name}  // Cooling fan")
            else:
                pin_defs.append(f"#define {comp_id}_PIN {pin_name}  // {comp_type}")
                
        return "\n".join(pin_defs)


# 测试代码
if __name__ == "__main__":
    library = CodeBlockLibrary()
    assembler = FirmwareAssembler(library)
    
    # 测试组件
    test_components = [
        {"type": "LED", "id": "LED1", "connected_to": "P1.0", "function": "status_indicator"},
        {"type": "SENSOR", "id": "TEMP1", "model": "LM35", "connected_to": "P1.5"},
        {"type": "FAN", "id": "FAN1", "connected_to": "P2.0"}
    ]
    
    # 测试功能
    test_functionality = {
        "description": "Temperature monitoring system that turns on fan when temperature exceeds 30C"
    }
    
    # 生成代码
    generated_code = assembler.assemble_firmware(test_components, test_functionality)
    
    # 输出加载的代码块
    print("加载的代码块:")
    for block_id in sorted(library.get_loaded_blocks()):
        print(f"- {block_id}")
        
    # 输出生成的代码前几行
    print("\n生成的代码预览:")
    preview_lines = generated_code.split("\n")[:20]
    for i, line in enumerate(preview_lines):
        print(f"{i+1:2d}: {line}") 