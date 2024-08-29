import os
import mido
import numpy as np

def midi2vec(midi, N, T): #, L_segs
    '''
    Crea un vector de longitud N que representa una duración total de T segundos.
    La asignación de valores se acopla al inicio de las casillas. Es decir
    `vec[i] -> comienzo del evento`
    `vec[i+1] -> Duración L_segs del evento` 
    Esto implica que si una nota deja de sonar en la casilla [i], esa casilla se marcará con "0", 
    pues se considera que consumió la casilla i-1 y terminó al inicio de la casilla i.
    NOTA: El tamaño del vector resultante puede ser de longitud menor a N.
    
    Parámetros:
        midi (MidiFile): Archivo MIDI a transformar
        N (int): Número ideal total de ventanas
        T (float): Duración total que representará el vector
        L_segs (float): Longitud temporal de cada ventana. Este valor será consistente con T/N.
                        
    Retorna:
        vector_midi (list): Vector MIDI codificado en 0,1,2 que marca silencios, inicios de nota
                            y notas sostenidas respectivamente.
    """
    '''

    # Retícula de separación de tiempos del vector
    time_grid = np.linspace(0, T, N+1)
    L_segs = time_grid[1] - time_grid[0]
    # print(L_segs)
    
    # Inicialización
    vector_midi = []

    for msg in midi:
        i = len(vector_midi)
        if not msg.is_meta:

            if msg.type == 'note_on' and msg.velocity > 0 and msg.time == 0:
                vector_midi.append(1)

            elif msg.type == 'note_on' and msg.velocity > 0 and msg.time > 0:
                # Si hay silencio antes del note_on
                num_silences = int(msg.time // L_segs)
                vector_midi.extend([0] * num_silences)
                
                # Agregar el valor 1 al vector. Se agrega al final de los [0] por que es cuando se ejecuta la nota
                vector_midi.append(1)

            elif msg.type == 'note_off' and msg.velocity == 0 and msg.time > 0:
                # Se busca ver si la nota sigue sonando por más de la primer ventana añadida con su respectivo 'note_on'

                if msg.time > L_segs: # Mayor que una celda
                    # Calcular el número de dos (nota sonando) a agregar
                    remaining_duration = msg.time - L_segs
                    num_notes_sounding = int(remaining_duration // L_segs)
                    vector_midi.extend([2] * num_notes_sounding)

    return vector_midi



###### Midi analysis ###############
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
        

###### Midi transformation ###############
def lstrip(midi):
    """
    Recorta el tiempo muerto antes de la primera nota en un archivo MIDI. 
    El recorte se hace "in place", es decir, el objeto original se modifica.
    
    Parámetros:
        midi (MidiFile): Archivo MIDI a recortar.
    
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






####################
# DEPRECATED
def ticks_to_microseconds(ticks, tempo, ticks_per_beat):

    microseconds_per_beat = tempo
    microseconds_per_tick = microseconds_per_beat / ticks_per_beat
    return ticks * microseconds_per_tick

# def midi2vec(file_path, L, tempo, ticks_per_beat):

#     midi = mido.MidiFile(file_path)

#     # for track in midi.tracks:
#     #     for msg in track:
#     #         if msg.type == 'set_tempo':
#     #             tempo = msg.tempo
#     #             break
    
#     sequence = []
#     current_time = 0  # seconds | DEPRECATED microseconds 
#     active_notes = {}  # note -> end time in microseconds
    
#     for track in midi.tracks:
#         track_time = 0  # ticks
        
#         for msg in track:
#             track_time += msg.time
#             current_time = mido.tick2second(track_time, ticks_per_beat, tempo) #ticks_to_microseconds(track_time, tempo, ticks_per_beat)
            
#             if msg.type == 'note_on' and msg.velocity > 0:
#                 note = msg.note
#                 start_time = current_time + mido.tick2second(msg.time, ticks_per_beat, tempo) #ticks_to_microseconds(msg.time, tempo, ticks_per_beat)
#                 active_notes[note] = start_time
#                 sequence.append(0)  # 0: note on
                
#             elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
#                 note = msg.note
#                 if note in active_notes:
#                     end_time = current_time
#                     start_time = active_notes[note]
#                     while start_time < end_time:
#                         if start_time + L <= end_time:
#                             sequence.append(1)  # 1: note sostenida
#                             start_time += L
#                         else:
#                             break
#                     del active_notes[note]
#                     sequence.append(2)  # 2: silencio
                    
#     return sequence


def process_midi_files(folder_path, L):

    all_sequences = {}
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        midi = mido.MidiFile(file_path)
        ticks_per_beat = midi.ticks_per_beat
        sequence = file_to_sequence(file_path, L, ticks_per_beat)
        all_sequences[filename] = sequence
            
    return all_sequences

# def midi2vec(midi, N, T, L_segs):
#     '''
#     Crea un vector de longitud N que representa una duración total de T segundos.
#     La asignación de valores se acopla al inicio de las casillas. Es decir
#     `vec[i] -> comienzo del evento`
#     `vec[i+1] -> Duración L_segs del evento` 
#     Esto implica que si una nota deja de sonar en la casilla [i], esa casilla se marcará con "0", 
#     pues se considera que consumió la casilla i-1 y terminó al inicio de la casilla i.
#     NOTA: El tamaño del vector resultante puede ser de longitud menor a N.
    
#     Parámetros:
#         midi (MidiFile): Archivo MIDI a transformar
#         N (int): Número ideal total de ventanas
#         T (float): Duración total que representará el vector
#         L_segs (float): Longitud temporal de cada ventana. Este valor será consistente con T/N.
                        
#     Retorna:
#         vector_midi (list): Vector MIDI codificado en 0,1,2 que marca silencios, inicios de nota
#                             y notas sostenidas respectivamente.
#     """
#     '''

#     # Retícula de separación de tiempos del vector
#     time_grid = np.linspace(0, T, N+1)
#     # time_grid_diffs = np.diff(time_grid)

#     # Inicialización
#     vector_midi = []
#     current_time = 0 # Tiempo acumulado
#     print('vector de inicio:', vector_midi, 'current_time:', current_time)

#     for msg in midi:
#         i = len(vector_midi)
#         if not msg.is_meta:
#             # Actualizar el tiempo acumulado
#             current_time += msg.time # Si se corre en midi.tracks: mido.tick2second(msg.time, midi.ticks_per_beat, midi.tracks[0].tempo)

#             if msg.type == 'note_on' and msg.velocity > 0:
#                 # Si hay silencio antes del note_on
#                 if current_time > time_grid[i]:
#                     # Calcular el número de silencios (etiqueta 0) a agregar
#                     silence_duration = current_time - time_grid[i]
#                     num_silences = int(silence_duration // L_segs)
#                     vector_midi.extend([0] * num_silences)
                
#                 # Agregar el valor 1 al vector. Se agrega al final de los [0] por que es cuando se ejecuta la nota
#                 vector_midi.append(1)
#                 print('vector:', vector_midi, 'current_time:', current_time, ' | timegrid:', time_grid[i])


#             elif msg.type == 'note_off' and msg.velocity == 0:
#                 # Se busca ver si la nota sigue sonando por más de la primer ventana añadida con su respectivo 'note_on'
#                 last_msg_endtime = time_grid[i] + L_segs
#                 if current_time > last_msg_endtime:
#                     # Calcular el número de dos (nota sonando) a agregar
#                     remaining_duration = current_time - last_msg_endtime
#                     num_notes_sounding = int(remaining_duration // L_segs)
#                     vector_midi.extend([2] * num_notes_sounding)

#                 print('vector:', vector_midi, 'current_time:', current_time, 'division:',num_notes_sounding, ' | timegrid:', time_grid[i], ' L+tgrid:', last_msg_endtime)

#         # current_time = time_grid[i+1]
#     return vector_midi