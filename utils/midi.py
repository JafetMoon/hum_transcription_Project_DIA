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


### Midi analysis

# Detecta MIDIs con "note_on" consecutivos en lugar de "note_on/note_off"
def detect_note_on_consecutives(midi):
    for track in midi.tracks:
        previous_note_on = None

        for msg in track:
            if msg.type == 'note_on' and previous_note_on:
                if msg.velocity == 0:
                    return True
            previous_note_on = msg if msg.type == 'note_on' else None

    return False

# Entrega características de la primer nota ejecutada
def first_note_data(midi):
    previous_msg = None
    tempo = None

    for msg in midi:
        # Guarda el tempo de la pista
        # Siempre se define antes que las notas, no habrá problema.
        if msg.type == 'set_tempo':
            tempo = msg.tempo

        if (msg.type == 'note_on') and (previous_msg not in ['note_on', 'note_in']):
            return (msg.note, tempo, msg.velocity, msg.time) 
        

### Midi transformation
def lstrip(midi):
    """
    Recorta el tiempo muerto antes de la primera nota en un archivo MIDI. 
    El recorte se hace "in place", es decir, el objeto original se modifica.
    
    Parámetros:
        midi (MidiFile): Ruta al archivo MIDI.
    
    Retorna:
        midi (MidiFile): Archivo MIDI modificado sin tiempo muerto al inicio.
    """
    
    # Recorrer las pistas y eventos del MIDI para eliminar el tiempo muerto al inicio
    for track in midi.tracks:
        total_time = 0
        for i, msg in enumerate(track):
            total_time += msg.time
            # Detectar el primer mensaje de 'note_on'
            if msg.type == 'note_on' and msg.time > 0:
                # Reducir el tiempo al primer 'note_on' a cero
                track[i].time = 0
                break
    
    return midi


def trim(midi, tempo, T):
    """
    Recorta el archivo MIDI a T segundos, eliminando cualquier nota sonando en el corte.
    
    Parámetros:
        midi (MidiFile): Archivo MIDI a recortar
        tempo (micro segundos): tiempo por negra (beat) en microsegundos
        T (float): Duración máxima en segundos del archivo MIDI.
    
    Retorna:
        new_midi (MidiFile): Archivo MIDI modificado con una duración máxima de T segundos.
    """
    
    
    # Convertir la duración T a ticks (tiempo del MIDI)
    ticks_per_beat = midi.ticks_per_beat
    ticks_per_second = ticks_per_beat * 1e6 / tempo
    max_ticks = int(T * ticks_per_second)

    # Crea el midi de salida
    new_midi = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    
    for track in midi.tracks:
        total_ticks = 0
        new_track = mido.MidiTrack()
        new_midi.tracks.append(new_track) 

        for msg in track:
            if msg.type == 'note_on' or msg.type == 'note_off':
                total_ticks += msg.time
                # print('time: ', msg.time, ' total_time: ', total_ticks)

            # Si está entro del rango de tiempo permitido, se agrega el mensaje
            if (total_ticks <= max_ticks) and (msg.type != 'end_of_track'):
                new_track.append(msg)
                last_msg = msg
            else:
                continue
        
        # Elimina notas iniciadas sin duración
        # Una nota completa empieza con note_on y termina con note_off
        if last_msg.type == 'note_on':
            new_track.pop()

    return new_midi
