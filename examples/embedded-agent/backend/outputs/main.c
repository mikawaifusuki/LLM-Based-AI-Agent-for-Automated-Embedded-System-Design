/**
 * Temperature Monitoring System with 8051 Microcontroller
 * 
 * This program reads temperature from LM35 sensor using ADC0804,
 * displays it on UART, and controls LED and cooling fan when
 * temperature exceeds 30°C threshold.
 */

#include <8051.h>
#include <stdio.h>

// Pin definitions
#define LED_PIN P1_0       // LED connected to P1.0
#define FAN_PIN P1_7       // Fan control via L293D at P1.7
#define ADC_CS  P2_0       // ADC0804 Chip Select
#define ADC_RD  P2_1       // ADC0804 Read
#define ADC_WR  P2_2       // ADC0804 Write
#define ADC_INTR P3_2      // ADC0804 Interrupt

// Constants
#define TEMP_THRESHOLD 30  // Temperature threshold in °C
#define ADC_DATA P0        // ADC data connected to P0

// Function prototypes
void uart_init(void);
void uart_transmit(unsigned char data);
void uart_print(char *str);
void delay_ms(unsigned int ms);
unsigned char read_adc(void);
float convert_to_temp(unsigned char adc_value);

void main() {
    unsigned char adc_value;
    float temperature;
    char temp_str[16];

    // Initialize UART
    uart_init();
    
    // Initialize pins
    LED_PIN = 0;      // Turn off LED initially
    FAN_PIN = 0;      // Turn off fan initially
    ADC_CS = 1;       // Deselect ADC initially
    ADC_RD = 1;       // Inactive RD
    ADC_WR = 1;       // Inactive WR
    
    uart_print("Temperature Monitoring System\r\n");
    uart_print("----------------------------\r\n");
    
    while (1) {
        // Read temperature from ADC
        adc_value = read_adc();
        
        // Convert ADC value to temperature
        temperature = convert_to_temp(adc_value);
        
        // Format temperature string for display
        sprintf(temp_str, "Temp: %.1f C\r\n", temperature);
        uart_print(temp_str);
        
        // Check if temperature exceeds threshold
        if (temperature > TEMP_THRESHOLD) {
            LED_PIN = 1;    // Turn on LED
            FAN_PIN = 1;    // Turn on fan
            uart_print("Alert: High temperature!\r\n");
        } else {
            LED_PIN = 0;    // Turn off LED
            FAN_PIN = 0;    // Turn off fan
        }
        
        // Wait for a second before next reading
        delay_ms(1000);
    }
}

/**
 * Initialize UART with 9600 baud rate
 * Assumes 11.0592 MHz crystal
 */
void uart_init(void) {
    SCON = 0x50;    // 8-bit, 1 stop bit, REN enabled
    TMOD = 0x20;    // Timer 1 in Mode 2 (auto-reload)
    TH1 = 0xFD;     // Reload value for 9600 baud with 11.0592MHz
    TR1 = 1;        // Start timer 1
}

/**
 * Transmit a byte via UART
 */
void uart_transmit(unsigned char data) {
    SBUF = data;    // Load data into buffer
    while (!TI);    // Wait until transmission complete
    TI = 0;         // Clear transmission flag
}

/**
 * Print a string via UART
 */
void uart_print(char *str) {
    while (*str) {
        uart_transmit(*str++);
    }
}

/**
 * Delay function (milliseconds)
 */
void delay_ms(unsigned int ms) {
    unsigned int i, j;
    for (i = 0; i < ms; i++) {
        for (j = 0; j < 123; j++); // Calibrated for approx 1ms delay at 11.0592MHz
    }
}

/**
 * Read value from ADC0804
 */
unsigned char read_adc(void) {
    unsigned char value;
    
    // Start conversion
    ADC_CS = 0;        // Select ADC
    ADC_WR = 0;        // Start conversion
    delay_ms(1);       // Short delay
    ADC_WR = 1;        // End pulse
    
    // Wait for conversion to complete
    while (ADC_INTR == 1);
    
    // Read the converted value
    ADC_RD = 0;        // Enable reading
    value = ADC_DATA;  // Read the data
    ADC_RD = 1;        // Disable reading
    ADC_CS = 1;        // Deselect ADC
    
    return value;
}

/**
 * Convert ADC value to temperature in Celsius
 * 
 * The LM35 produces 10mV/°C
 * With 5V reference, each ADC step is 5V/256 = 19.53mV
 * So temperature = ADC * 19.53 / 10 = ADC * 1.953
 */
float convert_to_temp(unsigned char adc_value) {
    return adc_value * 1.953;
} 