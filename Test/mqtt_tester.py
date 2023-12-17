import os
import logging.handlers
from Notifiers.MQTT.publisher import Publisher
import time
from Notifiers.MQTT.Secrets import TEST_SECRET

if __name__ == '__main__':
    log_format = '%(asctime)s %(name)s %(message)s'
    logging.basicConfig(format=log_format,
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)
    logger = logging.getLogger()

    directory_path = os.path.dirname(__file__)
    formatter = logging.Formatter(log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
    file_path = directory_path + '/debug.log'
    debug_log_handler = logging.handlers.TimedRotatingFileHandler(file_path, when='D', interval=1,
                                                                  backupCount=5, utc=True)
    debug_log_handler.setLevel(logging.DEBUG)
    debug_log_handler.setFormatter(formatter)
    logger.addHandler(debug_log_handler)

    logger.debug('Test logger')

    pub = Publisher(TEST_SECRET)

    big = 2

    for i in range(1000):
        delta = 3
        if i % 2 == 0:
            delta = -1
        big = big + delta

        message = {'Big': big, 'fat': 28, 'fake': 20}
        time_in_seconds = round(time.time() * 1000)
        time_stamped_message = {"ts": time_in_seconds - 50, "values": message}
        pub.send_message(str(time_stamped_message))
        time.sleep(5)

    pub.stop()


    # For testing the mqtt library
    # from Secrets import TEST_SECRET
    # if __name__ == '__main__':
    #     pub = Publisher(TEST_SECRET)
    #
    #     def send_missed_file():
    #         with open('data_not_sent_test.txt') as f:
    #             lines = f.readlines()
    #
    #         for line in lines:
    #             pub.send_message(line)
    #             time.sleep(1)
    #
    #     send_missed_file()
    #     pub.stop()
