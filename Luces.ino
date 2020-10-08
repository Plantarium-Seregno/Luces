// Luces.ino

// Firmware for the Arduino Leonardo board used by the Christmas light show project
// at Garden Tuttoverde (Seregno, Italy).
//
// Copyright © 2020, Plantarium Società Agricola


#include <USB-MIDI.h>

// Define Arduino pins used for connecting to the relay module.

#define RELAY_ONE   11
#define RELAY_TWO   10
#define RELAY_THREE 9
#define RELAY_FOUR  8
#define RELAY_FIVE  7
#define RELAY_SIX   6
#define RELAY_SEVEN 5
#define RELAY_EIGHT 4


USBMIDI_CREATE_DEFAULT_INSTANCE();

// -----------------------------------------------------------------------------

// This function will be automatically called when a NoteOn is received.
// It must be a void-returning function with the correct parameters,
// see documentation here:
// https://github.com/FortySevenEffects/arduino_midi_library/wiki/Using-Callbacks

void handleNoteOn(byte channel, byte pitch, byte velocity)
{
    // Do whatever you want when a note is pressed.

    // Try to keep your callbacks short (no delays ect)
    // otherwise it would slow down the loop() and have a bad impact
    // on real-time performance.

    digitalWrite(noteToRelay(pitch), LOW); // inverted logic
}

void handleNoteOff(byte channel, byte pitch, byte velocity)
{
    // Do something when the note is released.
    // Note that NoteOn messages with 0 velocity are interpreted as NoteOffs.

    digitalWrite(noteToRelay(pitch), HIGH); // inverted logic
}

int noteToRelay(int note)
{
    // Return the Arduino pin number corresponding to the given note.
    
    switch(note)
    {
        case 60: return RELAY_ONE;    // note C4 (middle C)
        case 61: return RELAY_TWO;    // C#4/Db4
        case 62: return RELAY_THREE;  // D4
        case 63: return RELAY_FOUR;   // D#4/Eb4
        case 64: return RELAY_FIVE;   // E4
        case 65: return RELAY_SIX;    // F4
        case 66: return RELAY_SEVEN;  // F#4/Gb4
        case 67: return RELAY_EIGHT;  // G4
    }
}

// -----------------------------------------------------------------------------

void setup()
{
    pinMode(RELAY_ONE, OUTPUT);
    pinMode(RELAY_TWO, OUTPUT);
    pinMode(RELAY_THREE, OUTPUT);
    pinMode(RELAY_FOUR, OUTPUT);
    pinMode(RELAY_FIVE, OUTPUT);
    pinMode(RELAY_SIX, OUTPUT);
    pinMode(RELAY_SEVEN, OUTPUT);
    pinMode(RELAY_EIGHT, OUTPUT);


    // Set all relays to OFF.
    // (inverted logic: HIGH level corresponds to OFF)
    digitalWrite(RELAY_ONE, HIGH);
    digitalWrite(RELAY_TWO, HIGH);
    digitalWrite(RELAY_THREE, HIGH);
    digitalWrite(RELAY_FOUR, HIGH);
    digitalWrite(RELAY_FIVE, HIGH);
    digitalWrite(RELAY_SIX, HIGH);
    digitalWrite(RELAY_SEVEN, HIGH);
    digitalWrite(RELAY_EIGHT, HIGH);
    
    // Connect the handleNoteOn function to the library,
    // so it is called upon reception of a NoteOn.
    MIDI.setHandleNoteOn(handleNoteOn);

    // Do the same for NoteOffs.
    MIDI.setHandleNoteOff(handleNoteOff);

    // Initiate MIDI communications, listen to all channels.
    MIDI.begin(MIDI_CHANNEL_OMNI);
}

void loop()
{
    // Call MIDI.read the fastest you can for real-time performance.
    MIDI.read();

    // There is no need to check if there are messages incoming
    // if they are bound to a Callback function.
    // The attached method will be called automatically
    // when the corresponding message has been received.
}
