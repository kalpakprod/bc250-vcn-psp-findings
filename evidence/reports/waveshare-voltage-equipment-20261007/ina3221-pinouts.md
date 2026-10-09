Title: Adafruit INA3221 Breakout

URL Source: https://learn.adafruit.com/adafruit-ina3221-breakout/pinouts

Published Time: 2024-10-23T13:36:08-04:00

Markdown Content:
7

Beginner

Product guide

## Pinouts

[![Image 1](https://cdn-learn.adafruit.com/assets/assets/000/133/213/medium800/adafruit_products_double.jpg?1729190983)](https://learn.adafruit.com/assets/133213)
Default I2C address is **0x40**.

## Power Pins

*   **VCC** - this is the power pin. To power the board, give it the same power as the logic level of your microcontroller - e.g. for a 5V micro like Arduino, use 5V. It can be powered between from 2.7 V to 5.5 V.
*   **GND** - common ground for power and logic.
*   **VPU** - this is the pull-up supply voltage pin. It is used to provide bias to the power valid (**VALID**) interrupt pin. Connect this pin to **VCC** to match the same logic level of your microcontroller.

## I2C Logic Pins

*   **SCL**- I2C clock pin, connect to your microcontroller's I2C clock line. This pin can use 3-5V logic, and there's a **10K pullup** on this pin.
*   **SDA**- I2C data pin, connect to your microcontroller's I2C data line. This pin can use 3-5V logic, and there's a**10K pullup** on this pin.
*   **[STEMMA QT](https://learn.adafruit.com/introducing-adafruit-stemma-qt) -**These connectors allow you to connect to development boards with **STEMMA QT** (Qwiic) connectors or to other things with [various associated accessories](https://www.adafruit.com/?q=JST%20SH%204).

## Input Channels

There are three input channels available on the INA3221: **VIN1**, **VIN2** and **VIN3**. Each input has a positive (**+**) and a negative (**-**) line. You'll connect your target power supplies to the positive line (**VIN1/2/3+**) and the loads to the negative ground line (**VIN1/2/3-**). These inputs are available as pins along the bottom of the board and via terminal blocks at the top; no soldering required.

You can measure high or low side current measuring up to +26VDC. The breakout will also report back the high side voltage, which is great for tracking battery life or solar panels. A precision amplifier measures the voltage across the built-in 0.05 ohm, 1% sense resistors. Since the amplifier maximum input difference is ±163.8mV, this means it can measure up to ±3.2 Amps. With the internal 13 bit ADC, the resolution at ±3.2A range is 0.4mA.

## Interrupts

*   **WRN** - This is the averaged measurement warning alert interrupt pin. This interrupt is triggered if the averaged current reading on any input channel exceeds a set threshold. If the interrupt is triggered, the **WRN** pin goes low.
*   **CRI** - This is the conversion-triggered critical alert interrupt pin. It detects overcurrent on any of the input channels. If the interrupt is triggered, the **CRI** pin goes low.
*   **TC** - This is the timing control alert interrupt pin. It signals if the power supplies connected to the input channels do not power up in the correct sequence. If one bus voltage doesn't reach its target level within a set time after another, the **TC** pin goes low.
*   **VALID** - This is the power valid alert interrupt pin. You can set an upper and lower limit threshold for this interrupt. When the upper limit interrupt is triggered, the pin goes high. When the lower limit interrupt is triggered, the pin goes low. You will need to connect the **VPU** pin to the same voltage as your microcontroller logic level (3V or 5V) to use the **VALID** interrupt.

## Address Jumper

*   **Addr** - On the front of the board, below the **INA3221 label** on the board silk, is the I2C address jumper. It is labeled **Addr** on the board silk. You can solder this jumper closed to change the I2C address to **0x41**. Otherwise, the I2C address is **0x40** when the jumper is open (default).

## Power LED and Jumper

*   **Power LED** - on the left side of the board, above the STEMMA QT connector, is the power LED, labeled**on**. It is a green LED.
*   **LED jumper** - on the front of the board, directly to the right of the power LED, is a jumper for the power LED. It is labeled**LED** on the board silk. If you want to disable the power LED, cut the trace on this jumper.

Page last edited October 23, 2024

Text editor powered by [tinymce](https://www.tiny.cloud/).
