# KilnControls

This code is based on https://github.com/jbruce12000/kiln-controller.
I wrote this because I wanted to be able to control ceramic kilns with mutilple heating zones. Most kilns, except very
small test kilns, have two or three control zones, like top middlle and bottom. This is true of both manually and
automatically controlled ceramic kilns. This software allows controlling one to four zones.

I also wanted to be able to change the UI and did not want to re-learn old web frameworks. The front
end (https://github.com/chipgarner/Kiln-Controls) uses React, which is state of the art now but will probably be an old
framework in a few years.

## Circuit Python

## Simulator

The simulator is elaborate. This is because it is the primary way of testing the code. It can also be used for experimenting with control methods. If you just want to run the
simulator to see what the program looks like in action you don't need to know much about it.

Each zone has it's own instance of KilnSimulator. The thermal model uses two lumped heat capacities, one for the
elements and one for the ware in the kiln. (This is the same as in the original
program, https://github.com/jbruce12000/kiln-controller) The elements are couple radiatively to the ware. Heat loss is
assumed to be by conduction and convection through the walls, top and bottom of the kiln. The zones are assumed to be
thermally connected to each other by radiation.

This seems to model the basic thermal characteristics of an electric kiln fairly well. Radiative heat transfer increases
with the fourth power of temperature, so it is much stronger at high temperatures. This means that the time it takes to
heat the elements and surrounding brick, and then radiate the heat to the ware, is much longer at low temperatures. This
change in the thermal time constant is a very important part of how the control system works.

Conduction and convection heat transfer inside the kiln are ignored. This is a very good approximation at high
temperatures, but not so good at low temperatures.

Heat transfer in a real kiln is much more complicated than this model, it is an attempt to include the most important
features in order to allow experimenting with control methods. The biggest weakness is that the control system only
measures the temperatures of the thermocouples and assumes this temperature is the same as the ware in the eintire zone.

## Notes and setup

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

install circuit
python, https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi
cd ~
sudo pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
pip3 install adafruit-circuitpython-max31855
pip3 install adafruit-circuitpython-max31856

You should now be able to run the simulator:
python3 mainSim.py