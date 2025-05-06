/**
 * 8051 Microcontroller Firmware - Common Function Declarations
 *
 * 此文件提供所有通用函数的声明
 */

#ifndef _COMMON_FUNCTIONS_H_
#define _COMMON_FUNCTIONS_H_

// System functions
void init_system(void);
void delay_ms(unsigned int ms);

// UART functions
void init_uart(void);
void uart_tx_char(char c);
void uart_tx_string(const char *str);
char uart_rx_char(void);
int uart_available(void);

// ADC functions
void init_adc(void);
unsigned char read_adc(void);
float read_temperature(void);
void adc_to_string(unsigned char value, char *buffer);
void float_to_string(float value, char *buffer, unsigned char precision);

// LED functions
void init_leds(void);
void led_on(unsigned char led_pin);
void led_off(unsigned char led_pin);
void led_toggle(unsigned char led_pin);

// Fan functions
void init_fan(void);
void fan_on(void);
void fan_off(void);
void control_fan_by_temp(float temperature, float threshold);

#endif // _COMMON_FUNCTIONS_H_ 