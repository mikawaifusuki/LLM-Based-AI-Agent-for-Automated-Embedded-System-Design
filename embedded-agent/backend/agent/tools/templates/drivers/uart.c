/**
 * UART Driver for 8051
 * 
 * 提供基本的串口通信功能
 */

// Function prototypes
void init_uart(void);
void uart_tx_char(char c);
void uart_tx_string(char *str);

/**
 * Initialize UART
 * 9600 baud assuming 11.0592MHz crystal
 */
void init_uart(void) {
    SCON = 0x50;   // Mode 1 (8-bit UART), REN=1 (enable receiver)
    TMOD &= 0x0F;  // Clear Timer 1 bits
    TMOD |= 0x20;  // Timer 1 in Mode 2 (8-bit auto-reload)
    TH1 = 0xFD;    // Reload value for 9600 baud with 11.0592MHz crystal
    TR1 = 1;       // Start Timer 1
    TI = 1;        // Set TI to indicate ready to transmit
}

/**
 * Transmit a character via UART
 */
void uart_tx_char(char c) {
    SBUF = c;      // Load character into buffer
    while (!TI);   // Wait for transmission to complete
    TI = 0;        // Clear transmission flag
}

/**
 * Transmit a string via UART
 */
void uart_tx_string(char *str) {
    while (*str) {
        uart_tx_char(*str++);
    }
} 