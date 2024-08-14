# SymphoSolids

## Move Solid. Create Music.

Designed for the M5StickCplus1/2, SymphoSolids consisits of three software components and a physical model that combine to form a musical rehabilitation devices that allows with limited mobility to create mosic, while boosting patient-to-patient engagement. This project provides the following necessary code and details to set-up, use and customize the SymphoSolid experience:

* **SymphoSolids_Main** is the main arduino file uploaded to the M5Stick. It regisyees acceltomeyer data and sends the coorepspining muscaal note as a Bluetooth LE Midi Command.
* **M5StickCplusBLE** is the arduino file uploaded used to first register face acceleromter data to the physical solid of choice. It is used in junction with **SymphoSolidsConfiguration**.
* **SymphoSolidsConfiguration** is a python GUI program that is used to name the device, assign face and note values, and modify existing face data structures.
  
### Watch a demo of the configuration and initialization process here!

video coming soon!

### Installation Guide
The easiest way to use SymphoSolids right away is by following the steps below:
1. Clone this project
2. * Download * *Arduino IDE* *
   * Install the appropriate version and follow the steps on https://www.arduino.cc/en/software
   * Once installed make sure to download the following libraries; BLEMIDI_Transport, M5StickCPlus2, M5StickCPlus and ESP32_NimBLE. For support downloading the libraries refer to https://docs.arduino.cc/software/ide-v1/tutorials/installing-libraries/








 
