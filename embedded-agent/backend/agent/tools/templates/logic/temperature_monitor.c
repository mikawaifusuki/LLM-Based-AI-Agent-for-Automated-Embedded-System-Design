/**
 * Temperature Monitoring Logic for 8051
 * 
 * 提供温度监控的基本逻辑
 */

// Function prototypes
void monitor_temperature(void);

/**
 * Monitor temperature and send via UART
 */
void monitor_temperature(void) {
    float temperature;
    char temp_str[16];
    
    // 读取温度
    temperature = read_temperature();
    
    // 转换为字符串并通过串口发送
    sprintf(temp_str, "Temp: %.1f C\r\n", temperature);
    uart_tx_string(temp_str);
    
    // 可以在此处添加温度控制逻辑的调用
    // 例如: control_fan_by_temperature(temperature);
} 