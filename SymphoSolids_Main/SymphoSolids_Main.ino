/*
Name: SymphoSolids Main for M5StickCPlus2
Author: Yahia Hassanen 
Date: Summer 2024
*/

//  HEADER
#include <BLEMIDI_Transport.h>
#include <M5StickCPlus2.h>
#include <hardware/BLEMIDI_ESP32_NimBLE.h>
#include "Config.h"
#include <cmath> 

#define MIDI_CHANNEL_NO 1
#define MIDI_DEVICE_NAME DEVICE_NAME

// Updated menu items
String menuItems[] = {"Normal Mode", "Mode 1", "Mode 2", "Mode 3", "Info"};
int currentSelection = 0;
const int totalItems = sizeof(menuItems) / sizeof(menuItems[0]);

BLEMIDI_CREATE_INSTANCE(MIDI_DEVICE_NAME, MIDI);
bool IsConnected = false;

float accX = 0.0F;
float accY = 0.0F;
float accZ = 0.0F;

int delayValue = 100;
int minDelay = 100;
int maxDelay = 1500;

void OnConnected() {
    IsConnected = true;
}

void OnDisconnected() {
    IsConnected = false;
}

void OnNoteOn(byte channel, byte note, byte velocity) {}
void OnNoteOff(byte channel, byte note, byte velocity) {}

void Normal_Mode() {
    StickCP2.Lcd.fillScreen(BLACK);
    while (true) {
        StickCP2.Imu.getAccelData(&accX, &accY, &accZ);
        StickCP2.Lcd.fillScreen(BLACK);
        StickCP2.Lcd.setCursor(10, 50);
        StickCP2.Lcd.print("Normal Mode");
        StickCP2.Lcd.setCursor(30, 90);
        StickCP2.Lcd.setTextColor(MAGENTA);
        StickCP2.Lcd.setTextSize(2);

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
            StickCP2.Lcd.printf("Face %d is up", matchedFace + 1);
        } else {
            StickCP2.Lcd.println("Undetermined");
        }

        StickCP2.Lcd.setTextColor(TFT_WHITE);
        StickCP2.update();
        if (StickCP2.BtnB.wasPressed()) {
            displayMenu();
            break;
        }
        delay(1000);
    }
}

// Updated musical modes
void playMusicalMode(int mode) {
    StickCP2.Lcd.fillScreen(BLACK);
    while (true) {
        StickCP2.Imu.getAccelData(&accX, &accY, &accZ);
        StickCP2.Lcd.fillScreen(BLACK);
        byte note = 0;
        StickCP2.Lcd.setCursor(10, 50);
        StickCP2.Lcd.printf("Mode %d", mode);
        StickCP2.Lcd.setCursor(30, 90);
        StickCP2.Lcd.setTextColor(MAGENTA);
        StickCP2.Lcd.setTextSize(2);

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
            StickCP2.Lcd.printf("Face %d is up", matchedFace + 1);
        } else {
            StickCP2.Lcd.println("Undetermined");
            note = 0;
        }

        StickCP2.Lcd.setTextColor(TFT_WHITE);

        if (note != 0) {
            MIDI.sendNoteOn(note, 100, MIDI_CHANNEL_NO);
            delay(delayValue);
            MIDI.sendNoteOff(note, 0, MIDI_CHANNEL_NO);
        }

        StickCP2.update();
        if (StickCP2.BtnB.wasPressed()) {
            displayMenu();
            break;
        }

        StickCP2.Lcd.setCursor(12, 30);
        StickCP2.Lcd.setTextColor(WHITE);
        StickCP2.Lcd.print("Tempo: ");
        StickCP2.Lcd.print(delayValue);

        if (StickCP2.BtnA.wasPressed()) {
            delayValue += 100;
            if (delayValue > maxDelay) {
                delayValue = minDelay;
            }
        }
        delay(100);
    }
}

void setup() {
    StickCP2.begin();
    Serial.begin(115200);
    StickCP2.Imu.init();
    StickCP2.Lcd.setRotation(3);
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setTextSize(2);

    MIDI.begin();

    BLEMIDI.setHandleConnected(OnConnected);
    BLEMIDI.setHandleDisconnected(OnDisconnected);

    MIDI.setHandleNoteOn(OnNoteOn);
    MIDI.setHandleNoteOff(OnNoteOff);
}

void loop() {
    StickCP2.update();

    if (Serial.available()) {
        String incomingMessage = Serial.readStringUntil('\n');
        Serial.println("Received: " + incomingMessage);
        Serial.println("Hello from M5StickC Plus!");
        delay(2000);

        if (incomingMessage == "Q") {
            Normal_Mode();
        } else if (incomingMessage == "Music") {
            playMusicalMode(currentSelection - 1);
        }
    }

    if (StickCP2.BtnA.wasPressed()) {
        currentSelection = (currentSelection + 1) % totalItems;
        displayMenu();
    }
    if (StickCP2.BtnB.wasPressed()) {
        selectOption();
    }
}

void displayExplanation() {
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setCursor(10, 20);
    StickCP2.Lcd.setTextSize(2);

    StickCP2.Lcd.print("Welcome to the DICE");
    StickCP2.Lcd.setCursor(10, 50);
    StickCP2.Lcd.print("Normal Mode sans music");
    StickCP2.Lcd.setCursor(10, 70);
    StickCP2.Lcd.print("Mode 1, 2, 3: Roll the dice, make music");
    StickCP2.Lcd.setCursor(10, 90);
}

void displayMenu() {
    StickCP2.Lcd.fillScreen(BLACK);

    int startY = 10;
    for (int i = 0; i < totalItems; i++) {
        if (i == currentSelection) {
            StickCP2.Lcd.setTextColor(GREEN);
        } else {
            StickCP2.Lcd.setTextColor(WHITE);
        }
        StickCP2.Lcd.setCursor(10, startY + (i * 20));
        StickCP2.Lcd.print(menuItems[i]);
    }
}

void selectOption() {
    switch (currentSelection) {
        case 0:
            Normal_Mode();
            break;
        case 1:
            playMusicalMode(1);  // Mode 1
            break;
        case 2:
            playMusicalMode(2);  // Mode 2
            break;
        case 3:
            playMusicalMode(3);  // Mode 3
            break;
        case 4:
            displayExplanation();
            break;
    }
}