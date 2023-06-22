# KilnControls
This code is based on https://github.com/jbruce12000/kiln-controller.
I wrote this because I wanted to be able to control ceramic kilns with mutilple heating zones. Most kilns, except very small test kilns, have two or three control zones, like top middlle and bottom. This is true of both manually and automatically controlled ceramic kilns. This software allows controlling one to four zones.

I also wanted to be able to change the UI and did not want to re-learn old web frameworks. The front end (https://github.com/chipgarner/Kiln-Controls) uses React, which is state pf the art now but will probably be an old framework in a few years.


FET wiring: https://elinux.org/RPi_GPIO_Interface_Circuits

Set up the Pi: https://raspberrytips.com/raspberry-pi-wifi-setup/

sudo apt update
sudo apt install git-all
sudo apt install python3-pip
sudo pip3 install --upgrade setuptools

git clone https://github.com/chipgarner/KilnControls.git
Navigate to KilnControls dirctory.
sudo pip3 install -r requirements.txt

sudo pip3 install gevent-websocket

install circuit python, https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi
cd ~
sudo pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
pip3 install adafruit-circuitpython-max31855
pip3 install adafruit-circuitpython-max31856

You should now be able to run the simulator:
python3 mainSim.py