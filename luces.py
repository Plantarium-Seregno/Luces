#!/usr/bin/env python3
"""Controller for Luces.

This plays a MIDI file and an audio file at the same time.

Based on this two examples:

* https://github.com/spatialaudio/jackclient-python/blob/master/examples/play_file.py 
* https://github.com/spatialaudio/jackclient-python/blob/master/examples/midi_file_player.py

"""
import sys
import argparse
from threading import Event, Thread
#from multiprocessing import Event, Process
import queue
import jack
from mido import MidiFile


#argv = iter(sys.argv)
#next(argv)
#filename = next(argv, '')
midi_file = '../src/Luces/Media/JingleBells.mid'
#connect_to = next(argv, '')
#if not filename:
#    sys.exit('Please specify a MIDI file')
try:
    mid = iter(MidiFile(midi_file))
except Exception as e:
    sys.exit(type(e).__name__ + ' while loading MIDI: ' + str(e))

audio_file = '../JingleBells/export/sessione_ffmpeg_mono.wav'

parser = argparse.ArgumentParser(description=__doc__)
#parser.add_argument('filename', help='audio file to be played back')
#parser.add_argument(
#    '-b', '--buffersize', type=int, default=20,
#    help='number of blocks used for buffering (default: %(default)s)')
#parser.add_argument('-c', '--clientname', default='file player',
#                    help='JACK client name')
#parser.add_argument('-m', '--manual', action='store_true',
#                    help="don't connect to output ports automatically")
manual = False
#args = parser.parse_args()
#if args.buffersize < 1:
#    parser.error('buffersize must be at least 1')

#client = jack.Client(args.clientname)
client = jack.Client('Luces')

blocksize = client.blocksize
samplerate = client.samplerate

midi_port = client.midi_outports.register('output')
midi_event = Event()
midi_msg = next(mid)
midi_fs = None  # sampling rate
midi_offset = 0

#q = queue.Queue(maxsize=args.buffersize)
q = queue.Queue(maxsize=20)
audio_event = Event()


def print_error(*args):
    print(*args, file=sys.stderr)


def stop_callback(msg=''):
    if msg:
        print_error(msg)
    for port in client.outports:
        port.get_array().fill(0)
    audio_event.set()
    raise jack.CallbackExit


def audio_process(frames):
    if frames != blocksize:
        stop_callback('blocksize must not be changed, I quit!')
    try:
        data = q.get_nowait()
    except queue.Empty:
        stop_callback('Buffer is empty: increase buffersize?')
    if data is None:
        stop_callback()  # Playback is finished
    for channel, port in zip(data.T, client.outports):
        port.get_array()[:] = channel


def midi_process(frames):
    global midi_offset
    global midi_msg
    midi_port.clear_buffer()
    while True:
        if midi_offset >= frames:
            midi_offset -= frames
            return  # We'll take care of this in the next block ...
        # Note: This may raise an exception:
        midi_port.write_midi_event(midi_offset, midi_msg.bytes())
        try:
            midi_msg = next(mid)
        except StopIteration:
            midi_event.set()
            raise jack.CallbackExit
        midi_offset += round(midi_msg.time * midi_fs)


@client.set_process_callback
def process(frames):
    try:
        audio_process(frames)
    except jack.CallbackExit:
        # proper handling recommended
        pass
    try:
        midi_process(frames)
    except jack.CallbackExit:
        # proper handling recommended
        pass


@client.set_samplerate_callback
def samplerate(samplerate):
    global midi_fs
    midi_fs = samplerate


@client.set_shutdown_callback
def shutdown(status, reason):
    print_error('JACK shutdown:', reason, status)
    audio_event.set()
    midi_event.set()


@client.set_xrun_callback
def xrun(delay):
    print_error("An xrun occured; increase JACK's period size?")
    print_error("Delay in microseconds:", delay)


#def shutdown(status, reason):
#    print_error('JACK shutdown!')
#    print_error('status:', status)
#    print_error('reason:', reason)
#    audio_event.set()


#client.set_xrun_callback(xrun)
#client.set_shutdown_callback(shutdown)
#client.set_process_callback(process)


def run_midi():
    with client:
        #if connect_to:
        #    port.connect(connect_to)
        print('Playing', repr(midi_file), '... press Ctrl+C to stop')
        try:
            midi_event.wait()
        except KeyboardInterrupt:
            print('\nInterrupted by user')


def run_audio():
    try:
        #import jack
        import soundfile as sf

        #with sf.SoundFile(args.filename) as f:
        with sf.SoundFile(audio_file) as f:
            for ch in range(f.channels):
                client.outports.register('out_{0}'.format(ch + 1))
            block_generator = f.blocks(blocksize=blocksize, dtype='float32',
                    always_2d=True, fill_value=0)
            #for _, data in zip(range(args.buffersize), block_generator):
            for _, data in zip(range(20), block_generator):
                q.put_nowait(data)  # Pre-fill queue
            with client:
                #if not args.manual:
                if not manual:
                    target_ports = client.get_ports(
                        is_physical=True, is_input=True, is_audio=True)
                    if len(client.outports) == 1 and len(target_ports) > 1:
                        # Connect mono file to stereo output
                        client.outports[0].connect(target_ports[0])
                        client.outports[0].connect(target_ports[1])
                    else:
                        for source, target in zip(client.outports,
                                target_ports):
                            source.connect(target)
                #timeout = blocksize * args.buffersize / samplerate
                timeout = blocksize * 20 / samplerate
                for data in block_generator:
                    q.put(data, timeout=timeout)
                q.put(None, timeout=timeout)  # Signal end of file
                audio_event.wait()  # Wait until playback is finished
    except KeyboardInterrupt:
        parser.exit('\nInterrupted by user')
    except (queue.Full):
        # A timeout occured, i.e. there was an error in the callback
        parser.exit(1)
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))


if __name__ == "__main__":
    #processes = [Process(target=run_audio), Process(target=run_midi)]
    threads = [Thread(target=run_audio), Thread(target=run_midi)]
    #threads = [Thread(target=run_midi)]
    #for p in processes:
    #    p.start()
    #for p in processes:
    #    p.join()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    #run_midi()
