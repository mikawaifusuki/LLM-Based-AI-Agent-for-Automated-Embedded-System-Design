/**
 * ADC0804 Driver for 8051
 * 
 * 提供ADC0804模数转换器的基本驱动
 */

// ADC0804接口定义
// 注意：需要根据实际硬件连接修改端口定义
#define ADC_DATA P1       // ADC数据端口 (默认使用P1)
#define ADC_CS   P3_0     // ADC片选信号
#define ADC_RD   P3_1     // ADC读信号
#define ADC_WR   P3_2     // ADC写信号
#define ADC_INTR P3_3     // ADC中断信号

// Function prototypes
void init_adc(void);
unsigned char read_adc(void);

/**
 * Initialize ADC0804
 */
void init_adc(void) {
    // 设置控制引脚为输出，中断引脚为输入
    ADC_CS = 1;   // 禁用ADC
    ADC_RD = 1;   // 读取未激活
    ADC_WR = 1;   // 写入未激活
}

/**
 * Read ADC value
 * @return 8-bit ADC value
 */
unsigned char read_adc(void) {
    unsigned char value;
    
    // 开始转换
    ADC_CS = 0;    // 使能ADC
    ADC_WR = 0;    // 开始转换
    ADC_WR = 1;    // 复位WR信号
    
    // 等待转换完成
    while (ADC_INTR);  // 等待INTR信号变为低电平
    
    // 读取转换结果
    ADC_RD = 0;    // 启用RD信号
    value = ADC_DATA;  // 读取数据
    ADC_RD = 1;    // 禁用RD信号
    ADC_CS = 1;    // 禁用ADC
    
    return value;
} 