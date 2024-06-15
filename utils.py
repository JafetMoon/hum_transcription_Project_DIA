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


def analizar_archivo(path):

    midi = mido.MidiFile(path)
    nota_liminf = float('inf')
    nota_limsup = float('-inf')
    notas_conteo = [0] * 128

    for track in midi.tracks:
        for msg in track:
            # velocity > 0 para no contar fin de ejecución
            if msg.type == 'set_tempo':
                tempo_ms = msg.tempo
            
            if msg.type == 'note_on' and msg.velocity > 0:
                nota = msg.note
                notas_conteo[nota] += 1

                if nota < nota_liminf:
                    nota_liminf = nota
                if nota > nota_limsup:
                    nota_limsup = nota

    freq_liminf = nota_a_frequencia(nota_liminf)
    freq_limsup = nota_a_frequencia(nota_limsup)
    cifrado_liming = nota_a_cifrado(nota_liminf)
    cifrado_limsup = nota_a_cifrado(nota_limsup)
    
    return (tempo_ms, nota_liminf, nota_limsup, freq_liminf, freq_limsup, cifrado_liming, cifrado_limsup, notas_conteo)







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
        info_archivo = extraer_info(filename)
        info_nota = analizar_archivo(path_archivo)
        data_archivo.append(info_archivo + list(info_nota[:-1]))
        data_notas.append([info_archivo[0]] + info_nota[-1])

    columns_notas = ['key'] + [f'{i} ({nota_a_cifrado(i)})' for i in range(128)]
    columns = ['key', 'Genero', 'PersonID', 'MusicID', 'SegmentID', 'RepetitionID', 'MetaID', 'tempo_ms',
               'LimInf_Nota', 'LimSup_Nota',
               'LimInf_Freq', 'LimSupFreq',
               'LimInf_Cifrado', 'LimSup_Cifrado']
    df_archivo = pd.DataFrame(data_archivo, columns=columns)
    df_notas = pd.DataFrame(data_notas, columns=columns_notas)
    return df_archivo, df_notas