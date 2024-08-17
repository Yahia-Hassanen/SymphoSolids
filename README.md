# SymphoSolids

## Move Solid. Create Music.

Designed for the M5StickCplus1/2, SymphoSolids consisits of three software components and a physical model that combine to form a musical rehabilitation devices that allows with limited mobility to create mosic, while boosting patient-to-patient engagement. This project provides the following necessary code and details to set-up, use and customize the SymphoSolid experience:

* **SymphoSolids_Main** is the main arduino file uploaded to the M5Stick. It regisyees acceltomeyer data and sends the coorepspining muscaal note as a Bluetooth LE Midi Command.
* **M5StickCplusBLE** is the arduino file uploaded used to first register face acceleromter data to the physical solid of choice. It is used in junction with **SymphoSolidsConfiguration**.
* **SymphoSolidsConfiguration** is a python GUI program that is used to name the device, assign face and note values, and modify existing face data structures.
  
### Watch a demo of the configuration and initialization process here!

[![Video Title](https://img.youtube.com/vi/L9C7AJwvAK8/0.jpg)](https://www.youtube.com/watch?v=L9C7AJwvAK8)


## First Time Installation Guide
The easiest way to use SymphoSolids right away is by following the steps below:
1. Clone this project
2. Download  *Arduino IDE* and associated libraries as needed
   * Install the appropriate version of *Arduino IDE* and follow the steps on https://www.arduino.cc/en/software
   * Once installed make sure to download the following libraries; BLEMIDI_Transport, M5StickCPlus2, M5StickCPlus and ESP32_NimBLE. For support downloading the libraries refer to https://docs.arduino.cc/software/ide-v1/tutorials/installing-libraries/

  ## User Guide
  **There are 3 stages before use.**

  ### Configuration
  1. Using a serial cable connect the M5Stick to laptop/computer.
  2. Open up the *M5StickCPlusBLE* file
  3. Ensuring the correct COM is chosen, upload the file to the stick pressibg the arrow on the top left corner.
     
**To Upload:**

 ![image](https://github.com/user-attachments/assets/31e575e4-a1f9-425f-922d-4757dcb90b0f)
 
**To switch COM:**

 ![image](https://github.com/user-attachments/assets/f933e13f-313c-4298-a5fc-768e4a337ea3)

  4. Run the SymphoSolidsConfiguration program.
  5. Using the GUI scan and connect to stick before initilazing the Solid's name, number of sides, face data and note values. For further detail watch the demo video attatched above.
  Note values are entered in MIDI values. MIDI values range from 0 to 127, where zero is silence and 127 is the highest pitch value of G9. Use the below conversion table adapted from Manaris et al.
Here is the completed table with the rest of the notes included:


| Note  | Value | Note  | Value | Note  | Value | Note  | Value |
|-------|-------|-------|-------|-------|-------|-------|-------|
| C_1   | 0     | CS_1  | 1     | DF_1  | 1     | D_1   | 2     |
| DS_1  | 3     | EF_1  | 3     | E_1   | 4     | ES_1  | 5     |
| FF_1  | 4     | F_1   | 5     | FS_1  | 6     | GF_1  | 6     |
| G_1   | 7     | GS_1  | 8     | AF_1  | 8     | A_1   | 9     |
| AS_1  | 10    | BF_1  | 10    | B_1   | 11    | BS_1  | 12    |
| CF0   | 11    | C0    | 12    | CS0   | 13    | DF0   | 13    |
| D0    | 14    | DS0   | 15    | EF0   | 15    | E0    | 16    |
| ES0   | 17    | FF0   | 16    | F0    | 17    | FS0   | 18    |
| GF0   | 18    | G0    | 19    | GS0   | 20    | AF0   | 20    |
| A0    | 21    | AS0   | 22    | BF0   | 22    | B0    | 23    |
| BS0   | 24    | CF1   | 23    | C1    | 24    | CS1   | 25    |
| DF1   | 25    | D1    | 26    | DS1   | 27    | EF1   | 27    |
| E1    | 28    | ES1   | 29    | FF1   | 28    | F1    | 29    |
| FS1   | 30    | GF1   | 30    | G1    | 31    | GS1   | 32    |
| AF1   | 32    | A1    | 33    | AS1   | 34    | BF1   | 34    |
| B1    | 35    | BS1   | 36    | CF2   | 35    | C2    | 36    |
| CS2   | 37    | DF2   | 37    | D2    | 38    | DS2   | 39    |
| EF2   | 39    | E2    | 40    | ES2   | 41    | FF2   | 40    |
| F2    | 41    | FS2   | 42    | GF2   | 42    | G2    | 43    |
| GS2   | 44    | AF2   | 44    | A2    | 45    | AS2   | 46    |
| BF2   | 46    | B2    | 47    | BS2   | 48    | CF3   | 47    |
| C3    | 48    | CS3   | 49    | DF3   | 49    | D3    | 50    |
| DS3   | 51    | EF3   | 51    | E3    | 52    | ES3   | 53    |
| FF3   | 52    | F3    | 53    | FS3   | 54    | GF3   | 54    |
| G3    | 55    | GS3   | 56    | AF3   | 56    | A3    | 57    |
| AS3   | 58    | BF3   | 58    | B3    | 59    | BS3   | 60    |
| CF4   | 59    | C4    | 60    | CS4   | 61    | DF4   | 61    |
| D4    | 62    | DS4   | 63    | EF4   | 63    | E4    | 64    |
| ES4   | 65    | FF4   | 64    | F4    | 65    | FS4   | 66    |
| GF4   | 66    | G4    | 67    | GS4   | 68    | AF4   | 68    |
| A4    | 69    | AS4   | 70    | BF4   | 70    | B4    | 71    |
| BS4   | 72    | CF5   | 71    | C5    | 72    | CS5   | 73    |
| DF5   | 73    | D5    | 74    | DS5   | 75    | EF5   | 75    |
| E5    | 76    | ES5   | 77    | FF5   | 76    | F5    | 77    |
| FS5   | 78    | GF5   | 78    | G5    | 79    | GS5   | 80    |
| AF5   | 80    | A5    | 81    | AS5   | 82    | BF5   | 82    |
| B5    | 83    | BS5   | 84    | CF6   | 83    | C6    | 84    |
| CS6   | 85    | DF6   | 85    | D6    | 86    | DS6   | 87    |
| EF6   | 87    | E6    | 88    | ES6   | 89    | FF6   | 88    |
| F6    | 89    | FS6   | 90    | GF6   | 90    | G6    | 91    |
| GS6   | 92    | AF6   | 92    | A6    | 93    | AS6   | 94    |
| BF6   | 94    | B6    | 95    | BS6   | 96    | CF7   | 95    |
| C7    | 96    | CS7   | 97    | DF7   | 97    | D7    | 98    |
| DS7   | 99    | EF7   | 99    | E7    | 100   | ES7   | 101   |
| FF7   | 100   | F7    | 101   | FS7   | 102   | GF7   | 102   |
| G7    | 103   | GS7   | 104   | AF7   | 104   | A7    | 105   |
| AS7   | 106   | BF7   | 106   | B7    | 107   | BS7   | 108   |
| CF8   | 107   | C8    | 108   | CS8   | 109   | DF8   | 109   |
| D8    | 110   | DS8   | 111   | EF8   | 111   | E8    | 112   |
| ES8   | 113   | FF8   | 112   | F8    | 113   | FS8   | 114   |
| GF8   | 114   | G8    | 115   | GS8   | 116   | AF8   | 116   |
| A8    | 117   | AS8   | 118   | BF8   | 118   | B8    | 119   |
| BS8   | 120   | CF9   | 119   | C9    | 120   | CS9   | 121   |
| DF9   | 121   | D9    | 122   | DS9   | 123   | EF9   | 123   |
| E9    | 124   | ES9   | 125   | FF9   | 124   | F9    | 125   |
| FS9   | 126   | GF9   | 126   | G9    | 127   |

  6. Once the desired number of faces are initilized with *xyz* data and note values. Use *Save File* and save file to the *SymphoSolids_Main* folder. 
   
WORK IN PROGRESS




  ## Citations
  [1]B. Manaris and A. R. Brown, Making Music with Computers. CRC Press, 2014.
‌








 
