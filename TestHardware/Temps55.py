# import Publish.publisher
import time
# from Secrets import TEST_SECRET
import logging
import board
import busio
import digitalio
import adafruit_max31855

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.info('Get the temperatures, MAX31855')

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs2 = digitalio.DigitalInOut(board.D5)

sensor2 = adafruit_max31855.MAX31855(spi, cs2)


def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0


publish_me = False


if publish_me:
    pass
    # pub = Publish.publisher.Publisher(TEST_SECRET)


    def publish_results(t2):
        message = {'T2 55': c_to_f(t2)}
        time_in_seconds = round(time.time() * 1000)
        time_stamped_message = {"ts": time_in_seconds, "values": message}
        pub.send_message(str(time_stamped_message))
else:
    def publish_results(t2):
        pass


last_t2 = 0  # Save this and re-use on errors
t2_cold_junction = -99

while True:
    try:
        temp2 = sensor2.temperature_NIST
        last_t2 = temp2
        t2_cold_junction = sensor2.reference_temperature
    except RuntimeError as ex:
        logging.error('Temp2 31855 crash: ' + str(ex))
        temp2 = last_t2

    logging.info('T2 55: {0:0.3f}F'.format(c_to_f(temp2)))
    logging.info('T2 cold junction: {0:0.3f}F'.format(c_to_f(t2_cold_junction)))
    logging.info('  ')

    publish_results(temp2)

    time.sleep(1)
