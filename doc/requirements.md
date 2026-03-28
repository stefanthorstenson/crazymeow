# TODO - still to be specified

In order of priority.

- State machine goes into Controller error very often
- yaw rate is lower than intended
- use commander instead of high-level commander to send speed setpoints
- controller outage should be increased
- go back to initializing if data is not ok
- update configure crazyflie to ask if the current URI should be used or if a new one should be written.
- requirements.txt file - can it be renamed?

# CrazyMeow software requirements specification

A toy version of the crazyflie, with a complete hardware setup to be able to fly. The focus of the CrazyMeow is ease of use and safety. A kid should be able to start the hardware and start flying.

## Document Info

| Field | Value |
|---|---|
| Version | 1.6 |

## Definitions

The system: All hardware parts and software parts, working together.

Software: All software components on the Raspberry Pi

Component: Highest level of software on Raspberry Pi, as an isolated piece of software.

## Parameters

<deadzone> = 5 %
<crazyflie_outage> = 0.5 seconds
<maximum_altitude_rate> = +-0.3 meters/second
<maximum_yaw_rate> = +-45 degrees/second
<maximum_speed_in_xy_plane> = +-1.0 meters/second
<maximum_altitude> = 1.2 meters

## Hardware

- Raspberry Pi with a Crazyradio 2.0
- Crazyflie 2.1 with Flow Deck v2
- Bluetooth controller

## System setup

This should be done by an experienced Crazyflie developer.

Manual setup is allowed, for example putting scripts in the correct place and pairing the bluetooth controller. Manual setup should be kept to a minimum.
Once manual setup is done, it should be possible to power cycle all hardware without having to do manual setup to be able to fly again.

All code will be committed to this repository, and it can therefore be assumed that the first step to set up the system is to clone this repo to the Raspberry Pi.

## Software

Overview of components:

- Crazypilot
- Controller mapping setup
- System setup helpers

All components will be on the Raspberry Pi

All components in this section are intended to run on the Raspberry Pi with Raspian OS.

### Crazypilot

The software that sends setpoint commands to the Crazyflie is called crazypilot.

It should be implemented in python.

It should use the crazyflie-lib-python for flight control.

The URI of the Crazyflie should be hard-coded in the software. Setting up URI should be part of manual setup.

Any log files produced that are older than 24 h should be removed.

#### Logging and debug mode

The crazypilot should log the following:

- 1 Hz readout of: current state, altitude, battery voltage, battery state, raw altitude axis value, and controller age (time in milliseconds since the last controller event was received).
- When the system is in Standby and altitude axis is above threshold, and takeoff condition is not met, the reason shall be printed, once for every time the altitude axis threshold is crossed from below to above.
- When the system goes into landing, the reason should be printed.

All log entries should have UTC timestamps.

Crazypilot should create one log file for every time crazypilot is started.

#### Debug mode

It should be possible to run crazypilot in debug mode.

In debug mode, crazypilot should send all log output to stdout as well.

### Controller mapping setup

There should be a separate CLI for setting up the controller and the controller mapping according to requirements.

### System setup helpers

This is a collection of tools to help set up the system. E.g. scripts to clone git repositories, setting up debugging and setting URI of Crazyflie.

These tools may use sudo calls. Before each sudo call, information should be printed to the user containing what the command using sudo will do.

These tools may use git clone. Before each git clone call, the user should be informed about what to clone and prompted for approval.

There should be a tool to:
- Write the radio address of the Crazyflie to the Crazyflie hardware, similar to the "Configure 2.x" in the Crazyflie client, which uses USB.
- Configure the URI of the Crazyflie to be used by Crazypilot

There should be a way to verify that the specified URI of the Crazyflie is correct. (Test connection).

There should be a tool to setup all services necessary to fulfill startup requirements.

Note: A tool may fulfill more than one requirement.

### External software components

- [Crazyflie firmware](https://github.com/bitcraze/crazyflie-firmware)
- [Crazyflie Python lib](https://github.com/bitcraze/crazyflie-lib-python/)
- [Crazyradio firmware](https://github.com/bitcraze/crazyradio-firmware)

## Startup

It should be possible to power on the raspberry pi, crazyflie and bluetooth controller in any order.

When all parts are powered on, the system should be able to fly.

Note: There is no need to signal that the system is ready.

## System states

The following subsections describe the different system states.

The system should start in state Initializing.

If any part of the system is rebooted, the system should go back to state Initializing.

The system should be able to handle that the Crazyflie shuts down and needs to be rebooted, without having to reboot any other hardware.

Note: The current implementation in the Crazyflie means that if the Raspberry Pi is rebooted after flying, the Crazyflie also needs to be rebooted before it can fly again. This is due to that the Crazyflie will end up in state Locked after not receiving set points, and the only way out is reboot.

### Initializing

When the system is starting up.

#### State exits

When

- all needed telemetry is received from the Crazyflie to the Raspberry Pi, and
- the Raspberry Pi is connected to the controller, and
- battery state is 0 (normal) (this means the Crazyflie is not plugged into a charger, and battery level is good)

the system shall go to state Standby.

### Standby

When the Crazyflie is on the ground and ready to take off.

Crazypilot should send no commands.

#### State exits

When 

- the user moves the joystick that corresponds to altitude to more than 50 % of positive maximum of the joystick, and
- the crazyflie reports that the battery is not low on power

the system should go into state Take-off.

If 

- not all needed telemetry is received from the Crazyflie to the Raspberry Pi, or
- battery state is not 0 (normal)

the system shall go to state Initializing.

### Take-off

During the take-off sequence, no controller input should affect the Crazyflie.

Take-off sequence:
- Crazypilot should commanded to go to altitude 0.4 m with 75 % of maximum allowed altitude rate. No movement in xy plane.

#### State exits

When the Crazyflie is on altitude above 0.35 m, the system should go into state Flying.

If data received from the crazyflie is incomplete for more than <crazyflie_outage>, the system should go into state Crazyflie error.

If the crazyflie reports battery is low on power.

### Flying

The crazyflie should be controlled using the hover-assist mode (as in the Crazyflie client)

This is how the controller should control the crazyflie:

- Left joystick up-down: Altitude rate (linear, <deadzone> deadzone, max <maximum_altitude_rate>)
- Left joystick left-right: Yaw rate (linear, <deadzone> deadzone, max <maximum_yaw_rate>)
- Right joystick up-down: Speed in x-direction (crazyflie body coordinate system), up in positive x direction (linear, <deadzone> deadzone, max <maximum_speed_in_xy_plane>)
- Right joystick left-right: Speed in y-direction (crazyflie body coordinate system), right should move the crazyflie to the right if the crazyflie is facing away from the pilot (x axis pointing away from the pilot) (linear, <deadzone> deadzone, max <maximum_speed_in_xy_plane>)

If there is a controller input outage, the crazypilot should keep sending the last command sent to the Crazyflie.

The commanded speed in xy plane shall be less than <maximum_speed_in_xy_plane>

Maximum commanded altitude is <maximum_altitude>.

#### State exits

When the Crazyflie is on an altitude below 0.2 m, the system should go into state Landing.

If the all controller input is zero for more than 10 seconds, the system should go into state Landing.

If data received from the crazyflie is incomplete for more than <crazyflie_outage>, the system should go into state Crazyflie error.

If controller input is not received from the bluetooth controller to the raspberry pi for more than 0.5 seconds, the system should go into state Controller error

If the crazyflie reports battery is low on power.

### Landing

Landing sequence:
- The crazypilot should command the crazyflie to decrease altitude by 0.1 meters/second, until the altitude is at 0.05 meters. 
- Send a landing command, if available, and otherwise stop sending commands.
- Set system to state Standby.

#### State exits

If data received from the crazyflie is incomplete for more than <crazyflie_outage>, the system should go into state Crazyflie error.

### Crazyflie error

The crazypilot should not send any commands.

#### State exits

When all necessary data from the crazyflie is received and it looks okay, the system should go into state Standby.

### Controller error

The crazypilot should command the crazyflie to stay on the same altitude as the last received command, with 0 velocity.

#### State exits

After 2.0 s in this state, the system should go to state Landing.

If the controller input is received, the system should go to state Flying.

If data received from the crazyflie is incomplete for more than <crazyflie_outage>, the system should go into state Crazyflie error.

## Debugging

It should be possible to connect to the Raspberry Pi via SSH. Setup may be part of manual setup.

## Safety

If the Crazyflie's reported altitude is greater than <maximum_altitude> + 0.3 meters for more than 1 second, the system should go into state Landing.

If the Crazyflie's reported speed in the xy plane is greater than <maximum_speed_in_xy_plane> + 0.2 meters/seconds for more than 1 second, the system should go into state Landing.

## Architecture and design requirements

The code should be well modularized and easy to maintain.

No code may run code that needs super user (sudo) priveleges.

No code may download from the internet (except installing packages using pip or apt-get).

It should be possible to run the crazypilot and the controller setup on a laptop with Ubuntu 24.04 and a Crazyradio 2.0 with minimum manual work.

Any Python should run from a Python virtual environment that is dedicated for this system.

Coordinate system:

- X: forward
- Y: left
- Z: up

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
- Requirements specifications, design specifications and test reports for all included software, to be placed in doc/

All guides should be placed in README.md

Requirements specifications, design specifications and test reports should have this information in the beginning:

Header: Document Info

| Field | Value |
|---|---|
| Software | <Software component name> |
| Version | <version number which corresponds to software specification> |
| Status | <draft/approved> |

When updating the version, the status must be set to draft.

Document heading should not be numbered.

Component requirements should have unique IDs.

Design documents 

## Other

This file may not be changed by a coding agent, unless specificly asked to. Suggestions can always be made, but not directly in the file.
