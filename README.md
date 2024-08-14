# SymphoSolids

## SymphoSolids is an interactive musical rehabilitative program designed for the M5StickCPlus1/2.

SymphoSolids consisits of three software components and a physical model that combine to form a musical rehabilitation devices that allows with limited mobility to create mosic, while boosting patient-to-patient engagement. This project provides the following necessary code and details to set-up, use and customize the SymphoSolid experience:

* **SymphoSolids_Main** is the main arduino file uploaded to the M5Stick. It regisyees acceltomeyer data and sends the coorepspining muscaal note as a Bluetooth LE Midi Command.
* **M5StickCplusBLE** is the arduino file uploaded used to first register face acceleromter data to the physical solid of choice. It is used in junction with **SymphoSolidsConfiguration**.
* **SymphoSolidsConfiguration** is a python GUI program that is used to name the device, assign face and note values, and modify existing face data structures.
  









 
