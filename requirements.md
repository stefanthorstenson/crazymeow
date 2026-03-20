# TODO - still to be specified

- Define take-off sequence.

# CrazyPie

A toy version of the crazyflie, with a complete hardware setup to be able to fly. The focus of the CrazyPie is ease of use and safety. A kid should be able to start the hardware and start flying.

## Terminology

The system: All hardware parts and software parts, working together.

## Hardware

Raspberry Pi with a Crazyradio 2.0
Crazyflie 2.1 with Flow Deck v2
Bluetooth controller

## Software

### Raspberry pi

Note that there may be other software on the raspberry pi, in order to fulfill requirements.

#### Crazypilot

The software that sends setpoint commands to the Crazyflie is called crazypilot.

It should be implemented in python.

It should use the crazyflie-lib-python for flight control.

The URI of the Crazyflie should be hard-coded in the software. Setting up URI should be part of manual setup.

Crazypilot should receive log data from the Crazyflie and write to log files. Log files older than 24 h should be removed.

### Crazyflie

The Crazyflie firmware should be non-modified crazyflie-firmware.

## System setup

This should be done by an experienced Crazyflie developer.

Manual setup is allowed, for example putting scripts in the correct place and pairing the bluetooth controller. Manual setup should be kept to a minimum.
Once manual setup is done, it should be possible to power cycle all hardware without having to do manual setup to be able to fly again.

All code will be committed to this repository, and it can therefore be assumed that the first step to set up the system is to clone this repo to the Raspberry Pi.

### Controller mapping setup

There should be a separate CLI for setting up the controller and the controller mapping according to requirements.

## Startup

It should be possible to power on the raspberry pi, crazyflie and bluetooth controller in any order.

When all parts are powered on, the system should be able to fly.

There is no need to signal that the system is ready.

## Flying

The crazyflie should be controlled using the hover-assist mode (as in the Crazyflie client)

This is how the controller should control the crazyflie:

- Left joystick up-down: Altitude rate (linear, 5 % deadzone, max +-0.3 meters/second)
- Left joystick left-right: Yaw rate (linear, 5 % deadzone, max +-45 degrees/second)
- Right joystick up-down: Speed in x-direction (crazyflie body coordinate system), up in positive x direction (linear, 5 % deadzone, max +-1.0 meters/second)
- Right joystick left-right: Speed in y-direction (crazyflie body coordinate system), right should move the crazyflie to the right if the crazyflie is facing away from the pilot (x axis pointing away from the pilot) (linear, 5 % deadzone, max +-1.0 meters/second)

## Error handling

If controller input is not received from the bluetooth controller to the raspberry pi, the following behaviour should be met:

- After 0.5 s of outage, the crazypilot should command the crazyflie to stay on the same altitude as the last received command, with 0 velocity.
- After 2.0 s of outage, the crazypilot should command the crazyflie to decrease altitude by 0.1 meters/second, until the altitude is at 0.15 meters. Then it should send a landing command, if available, and otherwise stop sending commands.

The system should be able to handle that the Crazyflie shuts down and needs to be rebooted, without having to reboot any other hardware.

## Debugging

It should be possible to connect to the Raspberry Pi via SSH. Setup may be part of manual setup.

### Restrictions

The crazyflie should only fly on an altitude below 1.2 meters.

Maximum speed in the xy-plane should be 1.0 meters/second.

## Architecture and design requirements

The code should be well modularized and easy to maintain.

No code may run code that needs super user priveleges.

No code may download from the internet (except installing packages using pip or apt-get).

It should be possible to run the crazypilot and the controller setup on a laptop with Ubuntu 24.04 and a Crazyradio 2.0 with minimum manual work.

## Process

At implementation of the system with this requirements specification, the following should also also be done:

- Requirements specification for each software should be created, with unique IDs for each requirement.
- Design specification for each software should be created, based on the requirements document.
- Each software should be tested against its requirements document. Output:
    Test reports (Pass, fail, cannot be tested)
    Test coverage statistics to requirements

Exceptions for testing:
- Process requirements
- Design and architecture requirements
- Documentation requirements

## Documentation

The documentation should include:

- Guide for how to setup the system (manual setup). This should include:
    - Installation of raspberry pi from off-the-shelf status to setting up all necessary parts for the system to work.
    - Pairing the bluetooth controller.
    - Setting up the controller mapping.
- Guide for testing the crazypilot and controller mapping setup on a laptop
- Guide for how to start flying
- Guide to debug
    - Path to log files

All guides should be placed in README.md
