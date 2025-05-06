/**
 * Fan Control Logic for 8051
 * 
 * 提供基于温度的风扇控制逻辑
 */

// Fan Pin definitions
// 默认引脚定义，实际使用时会被替换
// #define FAN1_PIN P1_2
// #define LED_INDICATOR_PIN P1_0

// Temperature threshold for fan control (默认阈值为30℃)
#define TEMP_THRESHOLD 30.0

// 函数原型
void init_fan(void);
void fan_on(void);
void fan_off(void);
void control_fan_by_temp(float temperature, float threshold);

/**
 * 初始化风扇控制
 */
void init_fan(void) {
    FAN1_PIN = 0;  // 初始关闭风扇
}

/**
 * 打开风扇
 */
void fan_on(void) {
    FAN1_PIN = 1;  // 打开风扇
    uart_tx_string("Fan ON\r\n");
}

/**
 * 关闭风扇
 */
void fan_off(void) {
    FAN1_PIN = 0;  // 关闭风扇
    uart_tx_string("Fan OFF\r\n");
}

/**
 * 基于温度控制风扇
 * 
 * @param temperature 当前温度值
 * @param threshold 开启风扇的温度阈值
 */
void control_fan_by_temp(float temperature, float threshold) {
    if (temperature > threshold) {
        // 温度高，开启风扇
        fan_on();
    } else {
        // 温度正常，关闭风扇
        fan_off();
    }
} 