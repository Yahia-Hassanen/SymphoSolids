/*
Name: SymphoSolids Main for M5StickCPlus2
Author: Yahia Hassanen 
Date: Summer 2024
*/

//  HEADER
#include <BLEMIDI_Transport.h>
#include <M5StickCPlus2.h>
#include <hardware/BLEMIDI_ESP32_NimBLE.h>

#define MIDI_CHANNEL_NO 1
#define MIDI_DEVICE_NAME "DICE"

// Menu variables
String menuItems[] = {"Normal Mode", "Musical Mode", "Info"};
int currentSelection = 0;
const int totalItems = sizeof(menuItems) / sizeof(menuItems[0]);

// BLEMIDI_CREATE_DEFAULT_INSTANCE()
BLEMIDI_CREATE_INSTANCE(MIDI_DEVICE_NAME, MIDI);

// BLE connect
bool IsConnected = false;

// INIT ACCELEROMETER
float accX = 0.0F;
float accY = 0.0F;
float accZ = 0.0F;

// pitch of note
#define INIT_NOTE_PITCH 30
int CurrentNotePitch = INIT_NOTE_PITCH;
#define PIN_LED 10

int delayValue = 100; // Initial delay value
int minDelay = 100;
int maxDelay = 1500;

// ====================================================================================
// Event handlers for incoming MIDI messages
// ====================================================================================

// Device connected
void OnConnected() {
  IsConnected = true;
}

// Device disconnected
void OnDisconnected() {
  IsConnected = false;
}

// Received note on
void OnNoteOn(byte channel, byte note, byte velocity) {}

// Received note off
void OnNoteOff(byte channel, byte note, byte velocity) {}

// Define Normal_Mode (sans music)
void Normal_Mode() {
  StickCP2.Lcd.fillScreen(BLACK);
  
  while (true) {
    StickCP2.Imu.getAccelData(&accX, &accY, &accZ);
    StickCP2.Lcd.fillScreen(BLACK);  // Clear the area where the text will be printed
    StickCP2.Lcd.setCursor(10, 50);
    StickCP2.Lcd.print("Normal Mode");
    if (accY > 0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 1 is up");
    } else if (accY < -0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 2 is up");
    } else if (accX > 0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 3 is up");
    } else if (accX < -0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 4 is up");
    } else if (accZ > 0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 5 is up");
    } else if (accZ < -0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 6 is up");
    } else {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Undetermined");
    }

    StickCP2.Lcd.setTextColor(TFT_WHITE); // Reset text color

    StickCP2.update();
    if (StickCP2.BtnB.wasPressed()) {
      displayMenu();
      break;
    }
    delay(1000); // Adjust delay as needed
  }
}

void Musical_Mode() {
  StickCP2.Lcd.fillScreen(BLACK);
  
  
  while (true) {
    StickCP2.Imu.getAccelData(&accX, &accY, &accZ);
    StickCP2.Lcd.fillScreen(BLACK);  // Clear the area where the text will be printed
    byte note = 0;
    StickCP2.Lcd.setCursor(10, 50);
    StickCP2.Lcd.print("Musical Mode");


    if (accY > 0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 1 is up");
      note = 33; // C3
    } else if (accY < -0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 2 is up");
      note = 35; // D3
    } else if (accX > 0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 3 is up");
      note = 40; // E3
    } else if (accX < -0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(YELLOW);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 4 is up");
      note = 45; // F3
    } else if (accZ > 0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 5 is up");
      note = 50; // G3
    } else if (accZ < -0.8) {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Face 6 is up");
      note = 47; // A3
    } else {
      StickCP2.Lcd.setCursor(30, 90);
      StickCP2.Lcd.setTextColor(MAGENTA);
      StickCP2.Lcd.setTextSize(2);
      StickCP2.Lcd.println("Undetermined");
      note = 0;
    }

    StickCP2.Lcd.setTextColor(TFT_WHITE); // Reset text color
    
    if (note != 0) {
      MIDI.sendNoteOn(note, 100, MIDI_CHANNEL_NO);
      delay(delayValue); // Play the note with the current delay
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
      // Increase delay value
      delayValue += 100;
      if (delayValue > maxDelay) {
        delayValue = minDelay; // Wrap around to minimum delay value
      }
    }
    delay(100); // Adjust delay as needed
  }
}


void setup() {
  // Initialize M5StickC Plus
  uint16_t vbat;
  StickCP2.begin();             // INIT M5StickC Plus
  Serial.begin(115200);
  StickCP2.Imu.init();          // INIT IMU
  StickCP2.Lcd.setRotation(3);  // ROTATE DISPLAY
  StickCP2.Lcd.fillScreen(BLACK);
  StickCP2.Lcd.setTextSize(2);
  
  

  // INIT MIDI
  MIDI.begin();
    
  // BLE connect Callback
  BLEMIDI.setHandleConnected(OnConnected);
    
  // BLE disconnect Callback
  BLEMIDI.setHandleDisconnected(OnDisconnected);

  // NoteON Callback
  MIDI.setHandleNoteOn(OnNoteOn);
  // NoteOff Callback
  MIDI.setHandleNoteOff(OnNoteOff);
  
}

void loop() {
  StickCP2.update();

  if (Serial.available()) { // Check if data is available to read
    String incomingMessage = Serial.readStringUntil('\n'); // Read the incoming data
    Serial.println("Received: " + incomingMessage); // Echo the received message
    Serial.println("Hello from M5StickC Plus!");
    delay(2000); // Delay to avoid spamming the serial monitor

    // Check the incoming message 
    if (incomingMessage == "Q") {
      Normal_Mode();    
      } 
    else if (incomingMessage == "Music") {
      Musical_Mode();
    }
  }
  // Check for button press
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

  StickCP2.Lcd.print("Welcome to the");
  StickCP2.Lcd.print("DICE");
  StickCP2.Lcd.setCursor(10, 50);
  StickCP2.Lcd.print("Normal Mode");
  StickCP2.Lcd.print("sans music");

  StickCP2.Lcd.setCursor(10, 70);
  StickCP2.Lcd.print("Musical Mode");
  StickCP2.Lcd.print("Roll the dice, make music");
  StickCP2.Lcd.setCursor(10, 90);
}

void displayMenu() {
  // Clear the screen
  StickCP2.Lcd.fillScreen(BLACK);
  
  // Draw the menu items lower on the screen
  int startY = 80;  // Adjust this value to lower the starting point of the menu
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
  // Execute a different function for each menu option
  switch (currentSelection) {
    case 0:
      Normal_Mode();
      break;
    case 1:
      Musical_Mode();
      break;
    case 2:
      displayExplanation();
      break;
  }
}
