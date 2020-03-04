# Adafruit NeoPixel library port to the rpi_ws281x library.
# Author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)
import atexit

import _rpi_ws281x as ws

def Color(red, green, blue, white = 0):
	"""Convert the provided red, green, blue color to a 24-bit color value.
	Each color component should be a value 0-255 where 0 is the lowest intensity
	and 255 is the highest intensity.
	"""
	return (white << 24) | (red << 16)| (green << 8) | blue


class _LED_Data(object):
	"""Wrapper class which makes a SWIG LED color data array look and feel like
	a Python list of integers.
	"""
	def __init__(self, channel, size):
		self.size = size
		self.channel = channel

	def __getitem__(self, pos):
		"""Return the 24-bit RGB color value at the provided position or slice
		of positions.
		"""
		# Handle if a slice of positions are passed in by grabbing all the values
		# and returning them in a list.
		if isinstance(pos, slice):
			return [ws.ws2811_led_get(self.channel, n) for n in xrange(*pos.indices(self.size))]
		# Else assume the passed in value is a number to the position.
		else:
			return ws.ws2811_led_get(self.channel, pos)

	def __setitem__(self, pos, value):
		"""Set the 24-bit RGB color value at the provided position or slice of
		positions.
		"""
		# Handle if a slice of positions are passed in by setting the appropriate
		# LED data values to the provided values.
		if isinstance(pos, slice):
			index = 0
			for n in xrange(*pos.indices(self.size)):
				ws.ws2811_led_set(self.channel, n, value[index])
				index += 1
		# Else assume the passed in value is a number to the position.
		else:
			return ws.ws2811_led_set(self.channel, pos, value)


class Adafruit_NeoPixel(object):
	def __init__(self, num, pin, freq_hz=800000, dma=5, invert=False,
			brightness=255, channel=0, strip_type=ws.WS2811_STRIP_RGB):
		"""Class to represent a NeoPixel/WS281x LED display.  Num should be the
		number of pixels in the display, and pin should be the GPIO pin connected
		to the display signal line (must be a PWM pin like 18!).  Optional
		parameters are freq, the frequency of the display signal in hertz (default
		800khz), dma, the DMA channel to use (default 5), invert, a boolean
		specifying if the signal line should be inverted (default False), and
		channel, the PWM channel to use (defaults to 0).
		"""
		# Create ws2811_t structure and fill in parameters.
		self._leds = ws.new_ws2811_t()

		# Initialize the channels to zero
		for channum in range(2):
			chan = ws.ws2811_channel_get(self._leds, channum)
			ws.ws2811_channel_t_count_set(chan, 0)
			ws.ws2811_channel_t_gpionum_set(chan, 0)
			ws.ws2811_channel_t_invert_set(chan, 0)
			ws.ws2811_channel_t_brightness_set(chan, 0)

		# Initialize the channel in use
		self._channel = ws.ws2811_channel_get(self._leds, channel)
		ws.ws2811_channel_t_count_set(self._channel, num)
		ws.ws2811_channel_t_gpionum_set(self._channel, pin)
		ws.ws2811_channel_t_invert_set(self._channel, 0 if not invert else 1)
		ws.ws2811_channel_t_brightness_set(self._channel, brightness)
		ws.ws2811_channel_t_strip_type_set(self._channel, strip_type)

		# Initialize the controller
		ws.ws2811_t_freq_set(self._leds, freq_hz)
		ws.ws2811_t_dmanum_set(self._leds, dma)

		# Grab the led data array.
		self._led_data = _LED_Data(self._channel, num)

		# Substitute for __del__, traps an exit condition and cleans up properly
		atexit.register(self._cleanup)

	def _cleanup(self):
		# Clean up memory used by the library when not needed anymore.
		if self._leds is not None:
			ws.delete_ws2811_t(self._leds)
			self._leds = None
			self._channel = None

	def begin(self):
		"""Initialize library, must be called once before other functions are
		called.
		"""
		resp = ws.ws2811_init(self._leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))

	def show(self):
		"""Update the display with the data from the LED buffer."""
		resp = ws.ws2811_render(self._leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))

	def setPixelColor(self, n, color):
		"""Set LED at position n to the provided 24-bit color value (in RGB order).
		"""
		self._led_data[n] = color

	def setPixelColorRGB(self, n, red, green, blue, white = 0):
		"""Set LED at position n to the provided red, green, and blue color.
		Each color component should be a value from 0 to 255 (where 0 is the
		lowest intensity and 255 is the highest intensity).
		"""
		self.setPixelColor(n, Color(red, green, blue, white))

	def setBrightness(self, brightness):
		"""Scale each LED in the buffer by the provided brightness.  A brightness
		of 0 is the darkest and 255 is the brightest.
		"""
		ws.ws2811_channel_t_brightness_set(self._channel, brightness)

	def getPixels(self):
		"""Return an object which allows access to the LED display data as if
		it were a sequence of 24-bit RGB values.
		"""
		return self._led_data

	def numPixels(self):
		"""Return the number of pixels in the display."""
		return ws.ws2811_channel_t_count_get(self._channel)

	def getPixelColor(self, n):
		"""Get the 24-bit RGB color value for the LED at position n."""
		return self._led_data[n]


# LED strip configuration:
LED_COUNT      = 8 * 32 * 4      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 1     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

"""
1016     ... 775
1017     ... 774
1018     ... 773
1019     ... 772
1020     ... 771
1021     ... 770
1022     ... 769
1023     ... 768

 512     ... 767
 513
 514
 515
 516
 517
 518
 519 520 ... 760

 504 503 ... 263
 505     ... 262
 506     ... 261
 507     ... 260
 508     ... 259
 509     ... 258
 510     ... 257
 511     ... 256

   0  15 ... 255
   1  14 ... 254
   2  13 ... 253
   3  12 ... 252
   4  11 ... 251
   5  10 ... 250
   6   9 ... 249
   7   8 ... 248

 x ->
y
|
v

"""

"""

B | ^
  | |
  | |
  v 0
  
A 0 ^
  | |
  | |
  v |
  
B | ^
  | |
  | |
  v 0

A 0 ^
  | |
  | |
  v |
"""

class DisplayMatrix(object):
    from functools import lru_cache
    """
    A +0 and +512
    x % 2 == 0: 8x + y
    x % 2 == 1: 8x + 7 - y
    
    B +256 and +768
    x % 2 == 0: 8(31 - x) + y
    x % 2 == 1: 8(31 - x) + 7 - y
    
    """
    @staticmethod
    @lru_cache(maxsize=1024)
    def _xy_to_n(x,y):
        ev = x % 2 == 0
        _y = y % 8

        if y < 8: # B + 768
            if ev:
                return 768 + 8 * (31 - x) + _y
            else:
                return 768 + 8 * (31 - x) + 7 - _y
        elif y < 16: # A + 512
            if ev:
                return 512 + 8 * x + _y
            else:
                return 512 + 8 * x + 7 - _y
        elif y < 24: # B + 256
            if ev:
                return 256 + 8 * (31 - x) + _y
            else:
                return 256 + 8 * (31 - x) + 7 - _y
        else: # A + 0
            if ev:
                return 0 + 8 * x + _y
            else:
                return 0 + 8 * x + 7 - _y

    def __init__(self, strip, x=32, y=32):
        self.strip = strip
        self.x = x
        self.y = y
        self.strip.begin()

    def __setitem__(self, xy, val):
        x, y = xy
        r, g, b = val
        self.strip.setPixelColorRGB(self._xy_to_n(x, y), g, r, b)

    def __getitem__(self, xy):
        x, y = xy
        return self.strip.getPixelColor(self._xy_to_n(x,y))

    def blank_display(self):
        for i in range(LED_COUNT):
            self.strip.setPixelColorRGB(i,0,0,0)

    def show(self):
        self.strip.show()


if __name__ == '__main__':
    import time
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    display = DisplayMatrix(strip)

    for i in range(LED_COUNT):
        strip.setPixelColorRGB(i,0,0,0)
    display.show()
    time.sleep(1)

    from snake import Game
    snake_game = Game('/dev/input/event0', display)
    snake_game.main_loop()
