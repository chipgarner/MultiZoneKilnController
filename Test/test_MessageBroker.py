import MessageBroker
import time

def test_profile_to_ms():
    mb = MessageBroker.MessageBroker()

    now = round(time.time() * 1000)
    profile = {'name': 'fast',
                         'segments': [{'time': 0, 'temperature': 100}, {'time': 3600, 'temperature': 100},
                                      {'time': 10800, 'temperature': 1000}, {'time': 14400, 'temperature': 1150},
                                      {'time': 16400, 'temperature': 1150}, {'time': 19400, 'temperature': 700}]}

    result = mb.profile_to_ms(profile)

    assert result['name'] == "fast"
    assert abs(now - result['segments'][0]['time_ms']) < 0.01
    assert result['segments'][5]['temperature'] == 700
    assert result['segments'][5]['time_ms'] - now == 19400000
    assert result['segments'][5]['time'] == 19400