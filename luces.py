#!/usr/bin/env python3
"""Controller for Luces.

This plays a MIDI file and an audio file at the same time.

Copyright © 2020, Plantarium Società Agricola
"""

import numpy as np
import threading
import jack
import soundfile as sf
from mido import MidiFile


client = jack.Client('Luces')

audio_out_port = client.outports.register('audio_out') # Mono
target_audio_port = client.get_ports(is_physical=True, is_input=True,
        is_audio=True)[0] # Soundcard Audio Output 1 (L)
midi_out_port = client.midi_outports.register('midi_out')
target_midi_port = client.get_ports('Leonardo', is_input=True,
        is_midi=True)[0] # TODO: put Arduino instead of jack-keyboard

media_dir = 'Media'
project = 'JingleBells'

audio_file = f'{media_dir}/{project}.wav'
midi_file = f'{media_dir}/{project}.mid'

audio_event = threading.Event()
midi_event = threading.Event()

audio_data, samplerate = sf.read(audio_file)
current_audio_frame = 0
midi_data = iter(MidiFile(midi_file))
midi_msg = next(midi_data)
fs = None # Sampling rate
offset = 0

def audio_process(frames):
    global current_audio_frame
    out_audio_data = audio_data[
            current_audio_frame:current_audio_frame+client.blocksize]

    if len(out_audio_data) == 0: # Playback is finished
        audio_out_port.get_array().fill(0)
        audio_event.set()

    # Last block
    # TODO: verify the case len(out_audio_data) == client.blocksize
    if len(out_audio_data) < client.blocksize:
        # Fill with zeros
        out_audio_data = np.append(out_audio_data,
                np.zeros(client.blocksize-len(out_audio_data)))

    audio_out_port.get_array()[:] = out_audio_data

    current_audio_frame += client.blocksize


def midi_process(frames):
    global offset
    global midi_msg
    midi_out_port.clear_buffer()
    while True:
        if offset >= frames:
            offset -= frames
            return
        midi_out_port.write_midi_event(offset, midi_msg.bytes())
        try:
            midi_msg = next(midi_data)
        except StopIteration:
            midi_event.set()
            raise jack.CallbackExit
        offset += round(midi_msg.time * fs)


@client.set_process_callback
def process(frames):
    try:
        audio_process(frames)
    except jack.CallbackExit:
        # TODO: proper handling recommended
        pass
    try:
        midi_process(frames)
    except jack.CallbackExit:
        # TODO: proper handling recommended
        pass


@client.set_samplerate_callback
def samplerate(samplerate):
    global fs
    fs = samplerate


with client:
    client.connect(audio_out_port, target_audio_port)
    client.connect(midi_out_port, target_midi_port)
    audio_event.wait() # Wait until playback is finished
    midi_event.wait()
