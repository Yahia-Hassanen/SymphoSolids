/*
Name: SymphoSolids Main for M5StickCPlus2
Author: Yahia Hassanen 
Date: Summer 2024
*/


#include <M5StickCPlus2.h>
#include <BLEMIDI_Transport.h>
#include <hardware/BLEMIDI_ESP32_NimBLE.h>
#include <string.h>
#include <stdio.h>


String receivedData;
char str1[] = "Q";


// BLE UUIDs
#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


// BLE Service and Characteristics
NimBLEServer *pServer;
NimBLEService *pService;
NimBLECharacteristic *pTxCharacteristic;
NimBLECharacteristic *pRxCharacteristic;


// Track connection state
bool isConnected = false;


// MIDI Definitions
#define MIDI_CHANNEL_NO 1
#define MIDI_DEVICE_NAME "M5SStickCPlus_1"
BLEMIDI_CREATE_INSTANCE(MIDI_DEVICE_NAME, MIDI);


// BLE connect
bool IsConnected = false;


#define INIT_NOTE_PITCH 30
int CurrentNotePitch = INIT_NOTE_PITCH;


int delayValue = 100; // Initial delay value
int minDelay = 100;
int maxDelay = 1500;


// Function prototypes
void handleM();
void handleQ();
void disconnect();
void onBLEWritten(NimBLECharacteristic *pCharacteristic);
void Normal_Mode();
void Musical_Mode();
void registerAccelData();


float accX = 0.0F;
float accY = 0.0F;
float accZ = 0.0F;


// Event handlers for incoming MIDI messages
void OnConnected() {
    IsConnected = true;
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setCursor(0, 0);
    StickCP2.Lcd.println("Connected successfully");
    Serial.println("Connected successfully");
}


void OnDisconnected() {
    IsConnected = false;
    NimBLEDevice::startAdvertising();
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setCursor(0, 0);
    StickCP2.Lcd.println("Waiting for connections...");
    Serial.println("Disconnected, waiting for connections...");
}


void OnNoteOn(byte channel, byte note, byte velocity) {}


void OnNoteOff(byte channel, byte note, byte velocity) {}


// BLE data received event handler
class MyCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic *pCharacteristic) {
        std::string value = pCharacteristic->getValue();
        receivedData = String(value.c_str()); // Convert std::string to String
       
        Serial.print("Received data: ");
        Serial.println(receivedData);


        // Print length of receivedData
        size_t length = receivedData.length(); // Use length() for String objects
        Serial.print("Length of receivedData: ");
        Serial.println(length);


        // Print ASCII values of receivedData
        Serial.println("ASCII values of receivedData:");
        for (size_t i = 0; i < length; i++) {
            Serial.print((int)receivedData.charAt(i));
            Serial.print(" ");
        }
        Serial.println(); // Print a new line after ASCII values
    }
};


class ServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer) {
        isConnected = true;
        OnConnected();  // Notify your application logic
    }


    void onDisconnect(NimBLEServer* pServer) {
        isConnected = false;
        OnDisconnected();  // Notify your application logic
    }
};


// Setup function
void setup() {
    // Initialize Serial for debugging
    Serial.begin(115200);


    // Initialize M5StickCPlus
    StickCP2.begin();
    StickCP2.Lcd.setRotation(3);
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setCursor(0, 0);
    StickCP2.Imu.init();  // INIT IMU


    MIDI.begin();
    // BLE connect Callback
    BLEMIDI.setHandleConnected(OnConnected);
   
    // BLE disconnect Callback
    BLEMIDI.setHandleDisconnected(OnDisconnected);


    // NoteON Callback
    MIDI.setHandleNoteOn(OnNoteOn);
    // NoteOff Callback
    MIDI.setHandleNoteOff(OnNoteOff);




    // Initialize BLE
    NimBLEDevice::init("M5StickCPlus_1");


    // Create BLE Server
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());


    // Create BLE Service
    pService = pServer->createService(SERVICE_UUID);


    // Create BLE Characteristics
    pTxCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID_TX,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );


    pRxCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID_RX,
        NIMBLE_PROPERTY::WRITE
    );


    // Set the event handler for received data
    pRxCharacteristic->setCallbacks(new MyCallbacks());


    // Start the service
    pService->start();


    // Start advertising
    NimBLEAdvertising *pAdvertising = NimBLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->start();


    // Initialize MIDI
    MIDI.begin();
    BLEMIDI.setHandleConnected(OnConnected);
    BLEMIDI.setHandleDisconnected(OnDisconnected);


    StickCP2.Lcd.println("Waiting for connections...");
    Serial.println("Setup complete, waiting for connections...");
}


// Loop function
bool inMusicalMode = false;


void loop() {
    StickCP2.update();  // Update M5 state
    Serial.println("Loop execution");
    delay(2000);


    if (receivedData.length() > 0) {
        Serial.print("Processing received data: ");
        Serial.println(receivedData);


        if (receivedData.equals("RegisterAccel")) {
            registerAccelData();
        } else if (receivedData.equals("Music")) {
            inMusicalMode = true;
            Musical_Mode();
        } else if (receivedData.equals("Q")) {
            StickCP2.Lcd.fillScreen(BLACK);
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(WHITE);
            StickCP2.Lcd.setTextSize(1);
            StickCP2.Lcd.println("QUIET");
            Serial.println("Entered Quiet mode");
        } else if (receivedData.equals("Disconnect")) {
            disconnect();
        } else if (receivedData.equals("ExitMusicMode")) {
            inMusicalMode = false;
        }
        receivedData = "";  // Reset received data after processing
    }
}


void registerAccelData() {
    // Implement your function to register accelerometer data
    Serial.println("Registered accelerometer data");
}


void disconnect() {
    NimBLEDevice::stopAdvertising();
    isConnected = false;
    receivedData = ""; // Reset received data
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setCursor(0, 0);
    StickCP2.Lcd.setTextColor(WHITE);
    StickCP2.Lcd.setTextSize(1);
    StickCP2.Lcd.println("Waiting for connections...");
    StickCP2.Lcd.println("Disconnected");
    Serial.println("Disconnected from device");
}


void Musical_Mode() {
    StickCP2.Lcd.fillScreen(BLACK);
    Serial.println("Entered Musical mode");
    while (inMusicalMode) {
        StickCP2.Imu.getAccelData(&accX, &accY, &accZ);
        StickCP2.Lcd.fillScreen(BLACK);
        byte note = 0;
        StickCP2.Lcd.setCursor(10, 50);
        StickCP2.Lcd.print("Musical Mode");
        if (accY > 0.8) {
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(CYAN);
            StickCP2.Lcd.setTextSize(2);
            StickCP2.Lcd.println("Note 1");
            note = 60;
            delayValue = 100;
        } else if (accY < -0.8) {
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(GREEN);
            StickCP2.Lcd.setTextSize(2);
            StickCP2.Lcd.println("Note 2");
            note = 62;
            delayValue = 200;
        } else if (accX > 0.8) {
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(YELLOW);
            StickCP2.Lcd.setTextSize(2);
            StickCP2.Lcd.println("Note 3");
            note = 64;
            delayValue = 300;
        } else if (accX < -0.8) {
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(RED);
            StickCP2.Lcd.setTextSize(2);
            StickCP2.Lcd.println("Note 4");
            note = 65;
            delayValue = 400;
        } else if (accZ > 0.8) {
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(BLUE);
            StickCP2.Lcd.setTextSize(2);
            StickCP2.Lcd.println("Note 5");
            note = 67;
            delayValue = 500;
        } else if (accZ < -0.8) {
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(PINK);
            StickCP2.Lcd.setTextSize(2);
            StickCP2.Lcd.println("Note 6");
            note = 69;
            delayValue = 600;
        } else {
            StickCP2.Lcd.setCursor(30, 90);
            StickCP2.Lcd.setTextColor(MAGENTA);
            StickCP2.Lcd.setTextSize(2);
            StickCP2.Lcd.println("No Note");
            delayValue = 1500;
        }
        StickCP2.Lcd.setTextColor(TFT_WHITE); // Reset text color
       
        if (note != 0) {
          MIDI.sendNoteOn(note, 100, MIDI_CHANNEL_NO);
          delay(delayValue); // Play the note with the current delay
          MIDI.sendNoteOff(note, 0, MIDI_CHANNEL_NO);
          }
        StickCP2.update();
        if (receivedData.equals("ExitMusicMode")) {
            inMusicalMode = false;
            Serial.println("Exited Musical mode");
            return;
        }
        delay(1000); // Adjust delay as needed
    }
}


