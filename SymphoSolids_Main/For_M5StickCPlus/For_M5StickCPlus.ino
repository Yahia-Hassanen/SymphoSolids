/*
Name: SymphoSolids Main for M5StickCPlus2
Author: Yahia Hassanen 
Date: Summer 2024
*/

//  HEADER
#include <BLEMIDI_Transport.h>
#include <M5StickCPlus.h>
#include <hardware/BLEMIDI_ESP32_NimBLE.h>
#include <cmath> 

#include "Dice.h" // MODIFY FILE NAME HERE!

#define MIDI_CHANNEL_NO 1
#define MIDI_DEVICE_NAME DEVICE_NAME

// Updated menu items
String menuItems[] = {"Mode 1", "Mode 2", "Mode 3", "Info"};
int currentSelection = 0;
const int totalItems = sizeof(menuItems) / sizeof(menuItems[0]);

BLEMIDI_CREATE_INSTANCE(MIDI_DEVICE_NAME, MIDI);
bool IsConnected = false;

float accX = 0.0F;
float accY = 0.0F;
float accZ = 0.0F;

int delayValue = 100;
int minDelay = 50;
int maxDelay = 300;

void OnConnected() {
    IsConnected = true;
}

void OnDisconnected() {
    IsConnected = false;
}

void OnNoteOn(byte channel, byte note, byte velocity) {}
void OnNoteOff(byte channel, byte note, byte velocity) {}


// Updated musical modes
void playMusicalMode(int mode) {
    M5.Lcd.fillScreen(BLACK);
    int previousDelayValue = delayValue; // Initialize to track delay changes

    while (true) {
        M5.IMU.getAccelData(&accX, &accY, &accZ);
        M5.Lcd.fillScreen(BLACK);
        byte note = 0;
        M5.Lcd.setCursor(10, 50);
        M5.Lcd.printf("Mode %d", mode);
        M5.Lcd.setCursor(30, 90);
        M5.Lcd.setTextColor(MAGENTA);
        M5.Lcd.setTextSize(2);

        float minAngle = M_PI;
        int matchedFace = -1;

        for (int i = 0; i < totalFaces; i++) {
            float dotProduct = accX * faceConfigs[i].x + accY * faceConfigs[i].y + accZ * faceConfigs[i].z;
            float magnitudeCurrent = sqrt(accX * accX + accY * accY + accZ * accZ);
            float magnitudeFace = sqrt(faceConfigs[i].x * faceConfigs[i].x + faceConfigs[i].y * faceConfigs[i].y + faceConfigs[i].z * faceConfigs[i].z);
            float angle = acos(dotProduct / (magnitudeCurrent * magnitudeFace));

            if (angle < minAngle) {
                minAngle = angle;
                matchedFace = i;
            }
        }

        if (matchedFace != -1) {
            switch (mode) {
                case 1:
                    note = faceConfigs[matchedFace].note1;
                    break;
                case 2:
                    note = faceConfigs[matchedFace].note2;
                    break;
                case 3:
                    note = faceConfigs[matchedFace].note3;
                    break;
            }
            M5.Lcd.printf("Face %d is up", matchedFace + 1);
        } else {
            M5.Lcd.println("Undetermined");
            note = 0;
        }

        M5.Lcd.setTextColor(TFT_WHITE);

        if (delayValue != previousDelayValue) {
            M5.Lcd.setCursor(12, 30);
            M5.Lcd.setTextColor(WHITE);
            M5.Lcd.print("DV: ");
            M5.Lcd.print(delayValue);
            previousDelayValue = delayValue; // Update the previous value
        }

        if (note != 0) {
            MIDI.sendNoteOn(note, 100, MIDI_CHANNEL_NO);
            delay(delayValue);
            MIDI.sendNoteOff(note, 0, MIDI_CHANNEL_NO);
        }

        M5.update();
        if (M5.BtnB.wasPressed()) {
            displayMenu();
            break;
        }


        if (M5.BtnA.wasPressed()) {
            delayValue += 50;
            if (delayValue > maxDelay) {
                delayValue = minDelay;
            }
        }
        delay(100);
    }
}

void setup() {
    M5.begin();
    Serial.begin(115200);
    M5.IMU.Init();
    M5.Lcd.setRotation(3);
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setTextSize(2);

    MIDI.begin();

    BLEMIDI.setHandleConnected(OnConnected);
    BLEMIDI.setHandleDisconnected(OnDisconnected);

    MIDI.setHandleNoteOn(OnNoteOn);
    MIDI.setHandleNoteOff(OnNoteOff);
}

void loop() {
    M5.update();

    if (Serial.available()) {
        String incomingMessage = Serial.readStringUntil('\n');
        Serial.println("Received: " + incomingMessage);
        Serial.println("Hello from M5StickC Plus!");
        delay(2000);
    }

    if (M5.BtnA.wasPressed()) {
        currentSelection = (currentSelection + 1) % totalItems;
        displayMenu();
    }
    if (M5.BtnB.wasPressed()) {
        selectOption();
    }
}

void displayExplanation() {
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(10, 20);
    M5.Lcd.setTextSize(2);

    M5.Lcd.print("Welcome to SymphoSolids");
    M5.Lcd.setCursor(10, 50);
    M5.Lcd.setCursor(10, 70);
    M5.Lcd.print("Mode 1, 2, 3: Roll the solid, make music");
    M5.Lcd.setCursor(10, 90);
}

void displayMenu() {
    M5.Lcd.fillScreen(BLACK);

    int startY = 10;
    for (int i = 0; i < totalItems; i++) {
        if (i == currentSelection) {
            M5.Lcd.setTextColor(GREEN);
        } else {
            M5.Lcd.setTextColor(WHITE);
        }
        M5.Lcd.setCursor(10, startY + (i * 20));
        M5.Lcd.print(menuItems[i]);
    }
}

void selectOption() {
    switch (currentSelection) {
        case 0:
            playMusicalMode(1);  // Mode 1
            break;
        case 1:
            playMusicalMode(2);  // Mode 2
            break;
        case 2:
            playMusicalMode(3);  // Mode 3
            break;
        case 3:
            displayExplanation();
            break;
    }
}