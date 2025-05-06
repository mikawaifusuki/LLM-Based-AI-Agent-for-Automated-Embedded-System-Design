/**
 * LM35 Temperature Sensor Driver for 8051
 * 
 * 提供LM35温度传感器的基本驱动
 */

// Function prototypes
float read_temperature(void);
unsigned char read_adc(void);  // 声明ADC读取函数，实际实现在adc0804.c

/**
 * Read temperature from LM35 sensor
 * @return Temperature in Celsius
 */
float read_temperature(void) {
    unsigned char adc_value;
    float temperature;
    
    // 读取ADC值
    adc_value = read_adc();
    
    // 转换为温度（单位：摄氏度）
    // LM35输出为10mV/°C
    // 假设5V参考电压，8位ADC (0-255)
    // temperature = adc_value * (5.0 / 256) * 100;
    temperature = adc_value * 0.196;  // 简化计算: 5/256*100 = 0.196
    
    return temperature;
} 