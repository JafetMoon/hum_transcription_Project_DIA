import os
import midi
import pandas as pd

def extraer_info(filename):
    """Extract information from the filename."""

    parts = filename.replace('.mid', '').split('_')
    person_id = parts[0]
    genero = person_id[0]
    return [filename] + [genero] + parts



def procesar_midis(path_carpeta):
    """Process all MIDI files in the given folder."""

    
    data = []
    for filename in os.listdir(path_carpeta):
        path_archivo = os.path.join(path_carpeta, filename)
        info_archivo = extraer_info(filename)
        info_nota = midi.analizar_archivo(path_archivo)
        data.append(info_archivo + list(info_nota))

    columns = ['key', 'Genero', 'PersonID', 'MusicID', 'SegmentID', 'RepetitionID', 'LimInf_Nota', 'LimSup_Nota', 'LimInf_Freq', 'LimSupFreq', 'LimInf_Cifrado', 'LimSup_Cifrado'] 
    df = pd.DataFrame(data, columns=columns)
    return df