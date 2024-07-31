/*
Name: SymphoSolids Configuration for M5StickCPlus2
Author: Yahia Hassanen 
Date: Summer 2024
*/

#include <M5StickCPlus2.h>
#include <Wire.h>
#include <BLEMIDI_Transport.h>
#include <hardware/BLEMIDI_ESP32_NimBLE.h>

// BLE UUIDs
#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

// MIDI Definitions
#define MIDI_CHANNEL_NO 1
#define MIDI_DEVICE_NAME "M5SStickCPlus2_1"
BLEMIDI_CREATE_INSTANCE(MIDI_DEVICE_NAME, MIDI);

String receivedData;
bool processDataFlag = false; // Flag to indicate processing of received data
bool processTest= false; // Flag to indicate test status

// BLE Service and Characteristics
NimBLEServer *pServer;
NimBLEService *pService;
NimBLECharacteristic *pTxCharacteristic;
NimBLECharacteristic *pRxCharacteristic;

// Track connection state
bool isConnected = false;

// Function prototypes
void disconnect();
void sendAccelData();

// Device connected
void OnConnected() {
    isConnected = true;
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setCursor(0, 0);
    StickCP2.Lcd.println("Connected successfully");
    Serial.println("Connected successfully");
}

// Device disconnected
void OnDisconnected() {
    isConnected = false;
    NimBLEDevice::startAdvertising();
    StickCP2.Lcd.fillScreen(BLACK);
    StickCP2.Lcd.setCursor(0, 0);
    StickCP2.Lcd.println("Waiting for connections...");
    Serial.println("Disconnected, waiting for connections...");
}

// BLE data received event handler
class MyCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic *pCharacteristic) {
        std::string value = pCharacteristic->getValue();
        receivedData = String(value.c_str()); // Convert std::string to String

        Serial.print("Received data: ");
        Serial.println(receivedData);

        if (receivedData.equals("Record")) {
          processDataFlag = true; // Set flag to process data
        }
        if (receivedData.equals("Test")){
          processTest = true;
          Serial.print("Processing Test");
        }
        else if (receivedData.equals("Disconnect")) {
            disconnect();
            receivedData = "";  // Reset received data after processing
            processDataFlag = false; // Reset flag
        }
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

void setup() {
    // Initialize M5StickC Plus2 and Serial
    StickCP2.begin();
    StickCP2.Imu.init();
    Serial.begin(115200);

    // BLE connect Callback
    BLEMIDI.setHandleConnected(OnConnected);
  
    // BLE disconnect Callback
    BLEMIDI.setHandleDisconnected(OnDisconnected);

    // Initialize BLE
    NimBLEDevice::init("M5StickCPlus2_1");

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

void loop() {
    StickCP2.update();  // Update M5 state
    delay(2000);

    if (processDataFlag) {
        sendAccelData(); // Send accelerometer data to the client
        processDataFlag = false; // Reset flag after processing
    }
    if (processTest){
      sendDot();
      processTest = false; // Reset flag after processing

    }
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

void sendAccelData() {
    float accelX, accelY, accelZ;
    StickCP2.Imu.getAccelData(&accelX, &accelY, &accelZ);

    byte data[12]; // 4 bytes for each float = 12 bytes total
    memcpy(data, &accelX, sizeof(float));
    memcpy(data + 4, &accelY, sizeof(float));
    memcpy(data + 8, &accelZ, sizeof(float));

    // Send the byte array to the BLE characteristic
    pTxCharacteristic->setValue(data, sizeof(data));
    pTxCharacteristic->notify(); // Notify client about the new data
    
    Serial.print("Sent accelerometer data: X=");
    Serial.print(accelX);
    Serial.print(", Y=");
    Serial.print(accelY);
    Serial.print(", Z=");
    Serial.println(accelZ);
}

void sendDot() {
    float accelX, accelY, accelZ;
    StickCP2.Imu.getAccelData(&accelX, &accelY, &accelZ);

    // Calculate the dot product with the unit vector (0, 0, 1)
    float dotProduct = accelZ; // Since the unit vector is (0, 0, 1), the dot product is simply accelZ

    byte data[4]; // 4 bytes for the float
    memcpy(data, &dotProduct, sizeof(float));

    // Send the byte array to the BLE characteristic
    pTxCharacteristic->setValue(data, sizeof(data));
    pTxCharacteristic->notify(); // Notify client about the new data
    
    Serial.print("Sent dot product: ");
    Serial.println(dotProduct);
}
