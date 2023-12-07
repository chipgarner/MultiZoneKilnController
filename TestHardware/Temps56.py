# import Publish.publisher
import time
# from Secrets import TEST_SECRET
import logging
import board
import busio
import digitalio
import adafruit_max31856

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.info('MAX31865 temperatures')

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs1 = digitalio.DigitalInOut(board.D6)

sensor1 = adafruit_max31856.MAX31856(spi, cs1)
sensor1.averaging = 16
sensor1.noise_rejection = 60
logging.info(str(sensor1.averaging))
logging.info(str(sensor1.noise_rejection))


def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0


publish_me = False


if publish_me:
    # pub = Publish.publisher.Publisher(TEST_SECRET)
    pass

    def publish_results(temp):
        message = {'T1 56': c_to_f(temp)}
        time_in_seconds = round(time.time() * 1000)
        time_stamped_message = {"ts": time_in_seconds, "values": message}
        # pub.send_message(str(time_stamped_message))
else:
    def publish_results(temp):
        pass

last_temp = 0

while True:
    sensor1.initiate_one_shot_measurement()
    time.sleep(1)
    temp1 = sensor1.unpack_temperature()
    temp1_cj = sensor1.unpack_reference_temperature()

    if last_temp == temp1:
        logging.error('Identical temperatures !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    last_temp = temp1

    for k, v in sensor1.fault.items():
        if v:
            logging.error('Temp1 31856 fault: ' + str(k))

    logging.info('T1 56: {0:0.3f}F'.format(c_to_f(temp1)))
    logging.info('T1 cold junction: {0:0.3f}F'.format(c_to_f(temp1_cj)))
    logging.info('  ')

    publish_results(temp1)

