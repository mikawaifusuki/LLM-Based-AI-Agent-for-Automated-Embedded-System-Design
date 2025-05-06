/**
 * LED Control Logic for 8051
 * 
 * 提供LED控制的基本逻辑
 */

// LED Pin definitions
#define LED1_PIN P1_0  // 默认使用P1.0，实际使用时需替换
#define LED2_PIN P1_1  // 默认使用P1.1，实际使用时需替换

// Function prototypes
void init_leds(void);
void led_on(unsigned char led_num);
void led_off(unsigned char led_num);
void led_toggle(unsigned char led_num);
void blink_led(unsigned char led_num, unsigned int delay_time);

/**
 * Initialize LEDs
 */
void init_leds(void) {
    LED1_PIN = 0;  // Turn off LED1 initially
    LED2_PIN = 0;  // Turn off LED2 initially
}

/**
 * Turn on specific LED
 */
void led_on(unsigned char led_num) {
    if (led_num == 1) {
        LED1_PIN = 1;
    } else if (led_num == 2) {
        LED2_PIN = 1;
    }
}

/**
 * Turn off specific LED
 */
void led_off(unsigned char led_num) {
    if (led_num == 1) {
        LED1_PIN = 0;
    } else if (led_num == 2) {
        LED2_PIN = 0;
    }
}

/**
 * Toggle specific LED
 */
void led_toggle(unsigned char led_num) {
    if (led_num == 1) {
        LED1_PIN = !LED1_PIN;
    } else if (led_num == 2) {
        LED2_PIN = !LED2_PIN;
    }
}

/**
 * Blink specific LED
 */
void blink_led(unsigned char led_num, unsigned int delay_time) {
    led_toggle(led_num);
    delay_ms(delay_time);  // 注: delay_ms函数在base_frame.c中定义
} 