from time import sleep_ms

class I2cLcd:
    """Implements a HD44780 character LCD connected via PCF8574 on I2C."""

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.backlight = 0x08  # Backlight ON by default
        self.PCF8574_GPIO = 0x00
        self.PCF8574_RS = 0x01
        self.PCF8574_RW = 0x02
        self.PCF8574_EN = 0x04
        self.PCF8574_BACKLIGHT = 0x08

        self.LCD_CLEAR = 0x01
        self.LCD_HOME = 0x02
        self.LCD_ENTRY_MODE = 0x04
        self.LCD_DISPLAY_CONTROL = 0x08
        self.LCD_CURSOR_SHIFT = 0x10
        self.LCD_FUNCTION_SET = 0x20

        self.LCD_ENTRY_RIGHT = 0x00
        self.LCD_ENTRY_LEFT = 0x02
        self.LCD_ENTRY_SHIFT_INC = 0x01
        self.LCD_ENTRY_SHIFT_DEC = 0x00

        self.LCD_DISPLAY_ON = 0x04
        self.LCD_DISPLAY_OFF = 0x00
        self.LCD_CURSOR_ON = 0x02
        self.LCD_CURSOR_OFF = 0x00
        self.LCD_BLINK_ON = 0x01
        self.LCD_BLINK_OFF = 0x00

        self.LCD_MOVE_LEFT = 0x00
        self.LCD_MOVE_RIGHT = 0x04

        self.LCD_4BIT_MODE = 0x00
        self.LCD_2LINE = 0x08
        self.LCD_1LINE = 0x00
        self.LCD_5x10_DOTS = 0x04
        self.LCD_5x8_DOTS = 0x00

        self._write_byte(0x00)
        sleep_ms(50)

        self._send_instruction(0x03)
        sleep_ms(5)
        self._send_instruction(0x03)
        sleep_ms(1)
        self._send_instruction(0x03)
        sleep_ms(1)
        self._send_instruction(0x02)

        self._send_instruction(self.LCD_FUNCTION_SET | self.LCD_4BIT_MODE | self.LCD_2LINE | self.LCD_5x8_DOTS)
        self._send_instruction(self.LCD_DISPLAY_CONTROL | self.LCD_DISPLAY_ON | self.LCD_CURSOR_OFF | self.LCD_BLINK_OFF)
        self.clear()
        self._send_instruction(self.LCD_ENTRY_MODE | self.LCD_ENTRY_LEFT | self.LCD_ENTRY_SHIFT_DEC)

    def _write_byte(self, data):
        self.i2c.writeto(self.i2c_addr, bytearray([data | self.backlight]))

    def _toggle_enable(self, data):
        sleep_ms(1)
        self._write_byte(data | self.PCF8574_EN)
        sleep_ms(1)
        self._write_byte(data & ~self.PCF8574_EN)
        sleep_ms(1)

    def _send_instruction(self, cmd):
        high_nibble = (cmd & 0xF0)
        low_nibble = ((cmd << 4) & 0xF0)
        self._write_byte(high_nibble)
        self._toggle_enable(high_nibble)
        self._write_byte(low_nibble)
        self._toggle_enable(low_nibble)

    def clear(self):
        self._send_instruction(self.LCD_CLEAR)
        sleep_ms(2)

    def putstr(self, string):
        for char in string:
            self._send_data(ord(char))

    def set_cursor(self, col, row):
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        self._send_instruction(0x80 | (col + row_offsets[row]))

    def _send_data(self, data):
        high_nibble = (data & 0xF0) | self.PCF8574_RS
        low_nibble = ((data << 4) & 0xF0) | self.PCF8574_RS
        self._write_byte(high_nibble)
        self._toggle_enable(high_nibble)
        self._write_byte(low_nibble)
        self._toggle_enable(low_nibble)

    def backlight_on(self):
        self.backlight = self.PCF8574_BACKLIGHT
        self._write_byte(0x00)

    def backlight_off(self):
        self.backlight = 0x00
        self._write_byte(0x00)
