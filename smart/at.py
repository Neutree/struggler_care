import time


if __name__ == "__main__":
    from Maix import GPIO
    from machine import UART
    from fpioa_manager import fm

    fm.register(0, fm.fpioa.GPIOHS1, force=True)
    wifi_io0_en=GPIO(GPIO.GPIOHS1, GPIO.OUT)
    wifi_io0_en.value(0)

    fm.register(7,fm.fpioa.UART2_TX)
    fm.register(6,fm.fpioa.UART2_RX)

    uart = UART(UART.UART2,115200,timeout=1000, read_buf_len=4096)
    time.sleep_ms(5000)
    uart.write("AT\r\n")
    print(uart.read())
    print("-----")
    
    
    uart.write("AT+TCSTOPSMART\r\n")
    while 1:
        read = uart.read()
        if read:
            print(read)


