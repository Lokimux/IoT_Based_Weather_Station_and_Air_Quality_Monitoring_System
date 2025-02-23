import struct
import time

class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        self.t_fine = 0
        self._read_calibration_data()
        self._configure_sensor()

    def _read_register(self, register, length=1):
        """Read bytes from a specific register."""
        return self.i2c.readfrom_mem(self.addr, register, length)

    def _write_register(self, register, value):
        """Write a byte to a specific register."""
        self.i2c.writeto_mem(self.addr, register, bytes([value]))

    def _read_calibration_data(self):
        """Read and parse calibration data from the sensor."""
        calib = self._read_register(0x88, 24)
        self.dig_T1, self.dig_T2, self.dig_T3 = struct.unpack('<Hhh', calib[0:6])
        self.dig_P1, self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9 = struct.unpack('<Hhhhhhhhh', calib[6:24])

    def _configure_sensor(self):
        """Set up the sensor in normal mode with standard settings."""
        self._write_register(0xF4, 0x27)  # Normal mode, temp and pressure oversampling x1
        self._write_register(0xF5, 0xA0)  # Standby time 1000ms, filter coefficient x4

    def _compensate_temperature(self, adc_T):
        """Compensate raw temperature data."""
        var1 = (((adc_T >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_T >> 4) - self.dig_T1) * ((adc_T >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        temperature = (self.t_fine * 5 + 128) >> 8
        return temperature / 100

    def _compensate_pressure(self, adc_P):
        """Compensate raw pressure data."""
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 += (var1 * self.dig_P5) << 17
        var2 += self.dig_P4 << 35
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            return 0  # Avoid division by zero
        pressure = 1048576 - adc_P
        pressure = (((pressure << 31) - var2) * 3125) // var1
        var1 = (self.dig_P9 * (pressure >> 13) * (pressure >> 13)) >> 25
        var2 = (self.dig_P8 * pressure) >> 19
        pressure = ((pressure + var1 + var2) >> 8) + (self.dig_P7 << 4)
        return pressure / 25600

    def _read_raw_data(self):
        """Read raw temperature and pressure data from the sensor."""
        raw = self._read_register(0xF7, 6)
        adc_P = (raw[0] << 16 | raw[1] << 8 | raw[2]) >> 4
        adc_T = (raw[3] << 16 | raw[4] << 8 | raw[5]) >> 4
        return adc_T, adc_P

    @property
    def temperature(self):
        """Get the compensated temperature in °C."""
        adc_T, _ = self._read_raw_data()
        return self._compensate_temperature(adc_T)

    @property
    def pressure(self):
        """Get the compensated pressure in hPa."""
        _, adc_P = self._read_raw_data()
        return self._compensate_pressure(adc_P)

    def altitude(self, sea_level_pressure=1013.25):
        """Calculate altitude based on pressure and sea level pressure."""
        pressure = self.pressure  # in hPa
        return 44330 * (1.0 - (pressure / sea_level_pressure) ** (1 / 5.255))
