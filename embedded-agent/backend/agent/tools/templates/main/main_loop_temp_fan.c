/**
 * Temperature Monitoring and Fan Control Main Loop for 8051
 * 
 * 提供温度监控和风扇控制的主循环逻辑
 */

#include <8051.h>
#include <stdio.h>

// 定义常量
#define CRYSTAL_FREQ 12000000
#define BAUD 9600

// 定义引脚
#define LED_PIN P1_0
#define TEMP_SENSOR_PIN P1_5
#define FAN_PIN P1_2

// 定义温度阈值
#define TEMP_THRESHOLD 30.0

// 函数原型
void init_uart(void);
void uart_tx_char(char c);
void uart_tx_string(const char *str);
float read_temperature(void);
void control_fan_by_temp(float temp, float threshold);
void delay_ms(unsigned int ms);
void init_adc(void);
void init_fan(void);
void init_leds(void);

void main(void) {
    float temperature;
    char temp_str[16];
    
    // 初始化
    init_uart();
    uart_tx_string("Temperature Monitoring System\r\n");
    uart_tx_string("---------------------------\r\n");
    init_adc();
    init_fan();
    init_leds();
    
    while(1) {
        // 读取温度
        temperature = read_temperature();
        
        // 转换为字符串并通过串口发送
        sprintf(temp_str, "Temp: %.1f C\r\n", temperature);
        uart_tx_string(temp_str);
        
        // 基于温度控制风扇
        control_fan_by_temp(temperature, TEMP_THRESHOLD);
        
        // 延时
        delay_ms(1000);  // 1秒延时
    }
}

// UART初始化
void init_uart(void) {
    // UART初始化代码
    P1_1 = 1; // TX引脚设置为输出
}

// 发送单个字符
void uart_tx_char(char c) {
    // 简单实现串口发送
    // 在实际应用中，这里会有UART寄存器操作
}

// 发送字符串
void uart_tx_string(const char *str) {
    while(*str) {
        uart_tx_char(*str++);
    }
}

// 读取温度
float read_temperature(void) {
    // 模拟温度读取
    return 25.0 + (P1_5 ? 5.0 : 0.0);  // 简单返回一个值
}

// 根据温度控制风扇
void control_fan_by_temp(float temp, float threshold) {
    if(temp >= threshold) {
        FAN_PIN = 1;  // 打开风扇
        LED_PIN = 1;  // 指示灯亮
    } else {
        FAN_PIN = 0;  // 关闭风扇
        LED_PIN = 0;  // 指示灯灭
    }
}

// 初始化ADC
void init_adc(void) {
    // ADC初始化代码
}

// 初始化风扇控制
void init_fan(void) {
    FAN_PIN = 0;  // 初始状态为关闭
}

// 初始化LED
void init_leds(void) {
    LED_PIN = 0;  // 初始状态为关闭
}

// 延时函数
void delay_ms(unsigned int ms) {
    unsigned int i, j;
    for(i = 0; i < ms; i++)
        for(j = 0; j < 120; j++);  // 大约1ms延时@12MHz
} 