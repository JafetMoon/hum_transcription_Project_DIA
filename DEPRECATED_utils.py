import os
import mido
import pandas as pd

def nota_a_frequencia(nota):

    return 440.0 * (2.0 ** ((nota - 69) / 12.0))


def nota_a_cifrado(nota):

    notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octava = nota // 12 - 1
    cifrado = notas_base[nota % 12]
    return f"{cifrado}{octava}"


def analizar_archivo(midi):
    """
    Analiza un archivo MIDI para obtener información sobre las notas.

    Args:
        midi: Objeto MidiFile cargado con la librería MIDO.

    Returns:
        Tuple (freq_liminf, freq_limsup, cifrado_liminf, cifrado_limsup):
        - freq_liminf: Frecuencia (Hz) de la nota más baja.
        - freq_limsup: Frecuencia (Hz) de la nota más alta.
        - cifrado_liminf: Cifrado (nombre de nota) de la nota más baja.
        - cifrado_limsup: Cifrado (nombre de nota) de la nota más alta.
    """
    nota_liminf = float('inf')
    nota_limsup = float('-inf')
    notas_conteo = [0] * 128
    tiempo_min = float('inf')

    for track in midi.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo_ms = msg.tempo
            
            # Frecuencia y nota mínima
            if msg.type == 'note_on' and msg.velocity > 0: # velocity > 0 para no contar fin de ejecución
                nota = msg.note
                notas_conteo[nota] += 1

                if nota < nota_liminf:
                    nota_liminf = nota
                if nota > nota_limsup:
                    nota_limsup = nota

            # Tiempo mínimo de nota
            if msg.type == 'note_off' and msg.velocity == 0: # velocity = 0 para encontrar errores en el estándar
                if msg.time < tiempo_min:
                    tiempo_min = mido.tick2second(msg.time, midi.ticks_per_beat, tempo_ms)  # [segs]

    # Mínima figura musical
    # tempo_ms
    quanta2figure = {4: 'redonda',
                    2: 'blanca',
                    1: 'negra',
                    1/2: 'corchea',
                    1/4: 'semicorchea',
                    1/8: 'fusa',
                    1/16: 'semifusa'}
    tempo_secs = tempo_ms / 10**6

    beat_quanta_min = tiempo_min / tempo_secs
    note_fig_min =  quanta2figure.get(beat_quanta_min, 0)

    freq_liminf = nota_a_frequencia(nota_liminf)
    freq_limsup = nota_a_frequencia(nota_limsup)
    cifrado_liming = nota_a_cifrado(nota_liminf)
    cifrado_limsup = nota_a_cifrado(nota_limsup)
    
    return (tempo_ms, tiempo_min, note_fig_min, nota_liminf, nota_limsup, freq_liminf, freq_limsup, cifrado_liming, cifrado_limsup), notas_conteo







def extraer_info(filename):

    file = filename.replace('.mid', '')
    parts = file.split('_')
    person_id = parts[0]
    genero = person_id[0]

    if len(parts) == 4:
        parts.append(None)

    return [file] + [genero] + parts



def procesar_midis(path_carpeta):

    
    data_archivo = []
    data_notas = []
    for filename in os.listdir(path_carpeta):
        path_archivo = os.path.join(path_carpeta, filename)
        midi = mido.MidiFile(path_archivo)

        info_archivo = extraer_info(filename)
        info_bounds, info_nota = analizar_archivo(midi)
        data_archivo.append(info_archivo + list(info_bounds))
        data_notas.append([info_archivo[0]] + info_nota)

    columns_notas = ['key'] + [f'{i} ({nota_a_cifrado(i)})' for i in range(128)]
    columns = ['key', 'Genero', 'PersonID', 'MusicID', 'SegmentID', 'RepetitionID', 'MetaID', 
               'tempo_ms', 'min_time', 'min_figure',
               'min_nota', 'max_nota',
               'min_freq', 'max_freq',
               'min_cifrado', 'max_cifrado']
    df_archivo = pd.DataFrame(data_archivo, columns=columns)
    df_notas = pd.DataFrame(data_notas, columns=columns_notas)
    return df_archivo, df_notas