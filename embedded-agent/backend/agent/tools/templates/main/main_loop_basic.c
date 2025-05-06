/**
 * Basic Main Loop for 8051
 * 
 * 提供一个基本的主循环，用于简单应用如LED闪烁
 */

#include <8051.h>

// 定义常量
#define CRYSTAL_FREQ 12000000

// 定义引脚
#define LED_PIN P1_0

// 函数原型
void init_uart(void);
void uart_tx_string(const char *str);
void init_leds(void);
void led_toggle(unsigned char led_num);
void delay_ms(unsigned int ms);

void main(void) {
    // 初始化
    init_uart();
    uart_tx_string("System initialized\r\n");
    init_leds();
    
    // 主循环
    while(1) {
        led_toggle(1); // 切换LED状态
        delay_ms(500); // 0.5秒延时
    }
}

// UART初始化
void init_uart(void) {
    // UART初始化代码
    P1_1 = 1; // TX引脚设置为输出
}

// 发送字符串
void uart_tx_string(const char *str) {
    // 简单实现，实际应用中需要完整的UART实现
    while(*str) {
        str++; // 仅用于展示
    }
}

// 初始化LED
void init_leds(void) {
    LED_PIN = 0; // 初始化为关闭状态
}

// 切换LED状态
void led_toggle(unsigned char led_num) {
    if(led_num == 1) {
        LED_PIN = !LED_PIN;
    }
}

// 延时函数
void delay_ms(unsigned int ms) {
    unsigned int i, j;
    for(i = 0; i < ms; i++)
        for(j = 0; j < 120; j++); // 大约1ms延时@12MHz
} 