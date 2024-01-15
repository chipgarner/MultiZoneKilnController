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

## Hardware Setup

FET wiring: https://elinux.org/RPi_GPIO_Interface_Circuits

## Software Setup

The software should run on a variety of boards that will run Circuit Python. I have tested this on the Raspberry Pi 3B.

Set up the Pi: https://raspberrytips.com/raspberry-pi-wifi-setup/

Enable SPI:

    sudo raspi-config
Select Interface Options. Select SPI, click Yes, seleft and click Finish.

For developers, the following setup instructions also work on Ubuntu. The simulator runs on ubuntu and is very useful for modifiying and testing code. 

Install the latest version of Raspberry Pi OS. These istructions assume Bookworm or later. Bookworm includes Python 3.11.2. Earlier versions may work but you will
need **Python 3.9 or greater**, and may also need to install git and pip and upgrade setuptools. (Bookworm comes with these.)

    sudo apt update
    sudo apt upgrade

Get the project:

    git clone https://github.com/chipgarner/MultiZoneKilnController.git

Navigate to KilnControls directory:

    cd Multi*

Create a virtual environment:

    python -m venv --system-site-packages env
    source env/bin/activate

Install dependencies:

    pip install -r requirements.txt

    sudo apt install python3-scipy

If everything has gone as planned the simulator should now run:

    python mainSim.py
You should see something like this:

2023-11-04 10:33:00,758 WARNING KilnSimulator: Running simulator. In case you thought otherwise.
2023-11-04 10:33:00,768 INFO Server: listening on 0.0.0.0:8081
2023-11-04 10:33:00,771 WARNING KilnSimulator: Running simulator. In case you thought otherwise.
2023-11-04 10:33:00,774 INFO __main__: Sim speed up factor is 100
2023-11-04 10:33:00,774 INFO __main__: Zone temps: {'Fred': 27, 'George': 27}
2023-11-04 10:33:00,777 INFO KilnZones: KilnZones running using 2 zones.
2023-11-04 10:33:00,781 INFO Controller: Controller initialized.

If you have the front end running you can interact with the simulator. See https://github.com/chipgarner/MultiZoneFrontEnd

You also now be able to run the main program:

    python mainPi.py
If you have one or more temperature sensors and thermocouples connected you should see the temperatures listed about once a second.

If you aare not familiar with python virtual environments (https://docs.python.org/3/library/venv.html) note that you 
must have the environment activated to run the program. Enter the following when inside the program directory:

    source env/bin/activate

Just enter deactivate if you need to exit the environment.