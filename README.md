# KilnControls

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
 
???? Not needed? sudo pip3 install adafruit-circuitpython-lis3dh

pip3 install adafruit-circuitpython-max31855
pip3 install adafruit-circuitpython-max31856

You should now be able to run the simulator:
python3 mainSim.py