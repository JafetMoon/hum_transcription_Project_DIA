import os
import mido
import numpy as np

def ticks_to_microseconds(ticks, tempo, ticks_per_beat):

    microseconds_per_beat = tempo
    microseconds_per_tick = microseconds_per_beat / ticks_per_beat
    return ticks * microseconds_per_tick

def file_to_sequence(file_path, L, ticks_per_beat):

    midi = mido.MidiFile(file_path)
    tempo = 500000  # default tempo (120 BPM)
    
    for track in midi.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break
    
    sequence = []
    current_time = 0  # microseconds
    active_notes = {}  # note -> end time in microseconds
    
    for track in midi.tracks:
        track_time = 0  # ticks
        
        for msg in track:
            track_time += msg.time
            current_time = ticks_to_microseconds(track_time, tempo, ticks_per_beat)
            
            if msg.type == 'note_on' and msg.velocity > 0:
                note = msg.note
                end_time = current_time + ticks_to_microseconds(msg.time, tempo, ticks_per_beat)
                active_notes[note] = end_time
                sequence.append(0)  # 0: note on
                
            elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
                note = msg.note
                if note in active_notes:
                    end_time = current_time
                    start_time = active_notes[note]
                    while start_time < end_time:
                        if start_time + L <= end_time:
                            sequence.append(1)  # 1: note sostenida
                            start_time += L
                        else:
                            break
                    del active_notes[note]
                    sequence.append(2)  # 2: silencio
                    
    return sequence

def process_midi_files(folder_path, L):

    all_sequences = {}
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        midi = mido.MidiFile(file_path)
        ticks_per_beat = midi.ticks_per_beat
        sequence = file_to_sequence(file_path, L, ticks_per_beat)
        all_sequences[filename] = sequence
            
    return all_sequences

