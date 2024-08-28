import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display


def trim(audio, sr, T_midi, T_audio=None):
    """
    Recorta un audio eliminando partes en silencio al inicio y final,
    y luego lo corta a la duración de T_midi.
    
    Parámetros:
        audio (np.ndarray): Array de audio cargado con librosa.
        sr (int): Frecuencia de muestreo del audio.
        T_midi (float): Duración del MIDI equivalente transformado que funciona como plantilla.
        T_audio (float): Duración del audio de entrada.
    
    Retorna:
        audio_recortado (np.ndarray): Audio recortado a la duración de T_midi.
    """
    # Eliminar partes en silencio al inicio y final
    audio_trimmed, _ = librosa.effects.trim(audio, top_db=50) # top_db 2 desviaciones
    # Calcular la cantidad de muestras correspondiente a T_midi
    max_samples = int(np.ceil(T_midi * sr))
    # Recortar el audio a T_midi
    audio_recortado = audio_trimmed[:max_samples]

    # if T_midi < T_audio:
    #     return audio
    
    return audio_recortado


def dividir_en_ventanas(audio, sr, L_seg):
    """
    Divide un audio en ventanas de longitud L_seg.
    
    Parámetros:
        audio (np.ndarray): Array de audio cargado.
        sr (int): Frecuencia de muestreo del audio.
        L_seg (float): Duración de cada ventana en segundos.
    
    Retorna:
        audio_frames (np.ndarray): Array de (ventanas, muestras).
        L (int): Cantidad de muestras por ventana.
    """
    # Convertir la duración de la ventana (L en segundos) a muestras
    L = int(sr * L_seg)
    
    # Dividir la señal de audio en ventanas de longitud L
    audio_frames = librosa.util.frame(audio, frame_length=L, hop_length=L)
    
    return audio_frames, L


def espectrograma(audio, sr, L, freq_range):
    """
    Genera un espectrograma a partir de un audio recortado y devuelve su representación en array.
    
    Parámetros:
        audio (np.ndarray): Array de audio.
        sr (int): Frecuencia de muestreo del audio.
        L (int): Cantidad de muestras por ventana.
        freq_range (tuple): Rango de frecuencias a considerar (min_freq, max_freq).
    
    Retorna:
        S_filtered_db (np.ndarray): Espectrograma en decibelios filtrado por las frecuencias requeridas.
        freqs_filtered (np.ndarray): Valores de frecuencia restantes
    """
    min_freq, max_freq = freq_range
    
    # Generar el espectrograma usando Short-Time Fourier Transform (STFT)
    S = librosa.stft(audio, n_fft=L, hop_length=L)
    S_magnitude = np.abs(S)
    
    # Obtener las frecuencias correspondientes a los índices
    freqs = librosa.fft_frequencies(sr=sr, n_fft=L)
    
    # Obtener los índices que corresponden a las frecuencias requeridas
    min_index = np.argmax(freqs >= min_freq)
    max_index = np.argmax(freqs > max_freq) - 1
    
    # Filtrar el espectrograma por el rango de frecuencias
    S_filtered = S_magnitude[min_index:max_index, :]
    freqs_filtered = freqs[min_index:max_index]

    # Convertir el espectrograma a decibelios
    S_filtered_db = librosa.amplitude_to_db(S_filtered, ref=np.max)
    
    return S_filtered_db, freqs_filtered




##### 4 
# Función para extraer los onsets del archivo de audio
def extract_audio_onsets(audio_path):
    # Cargar el archivo de audio
    y, sr = librosa.load(audio_path)
    
    # Detección de onsets
    onset_times = librosa.onset.onset_detect(y=y, sr=sr, backtrack=False, units='time')
    
    return onset_times


##################################
########### DEPRECATED ###########
def process_audio_files(folder_path, L):

    sample_rate = 22050
    n_fft = int((L * sample_rate) / 1000)
    hop_length = int(n_fft / 4)
    spectrograms = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.wav'):
            file_path = os.path.join(folder_path, filename)
            y, sr = librosa.load(file_path, sr=sample_rate)

            # Calcular la STFT
            stft_result = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)

            # Convertir el espectrograma a dB
            spectrogram_db = librosa.amplitude_to_db(np.abs(stft_result), ref=np.max)

            # Guardar el espectrograma como imagen
            save_spectrogram(file_path, spectrogram_db, sr, hop_length)

            spectrograms.append(stft_result)
        
    return spectrograms

def save_spectrogram(file_path, spectrogram_db, sr, hop_length):

    plt.figure(figsize=(10, 6))
    librosa.display.specshow(spectrogram_db, sr=sr, hop_length=hop_length, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Espectrograma de STFT de {os.path.basename(file_path)}')
    
    # Save the figure
    output_filename = os.path.splitext(file_path)[0] + '_spectrogram.png'
    plt.savefig(output_filename)
    plt.close()

# Función para ajustar el desfase entre audio y MIDI usando el onset
## DEPRECATED
def DEPRECATED_align_midi_to_audio(midi_path, audio_onsets, threshold=0.05):
    import mido
    midi = mido.MidiFile(midi_path)
    midi_onsets = extract_midi_onsets(midi_path)
    
    # Calcular el desfase entre el primer onset del audio y del MIDI
    onset_diff = audio_onsets[0] - midi_onsets[0]
    
    # Ajustar el tiempo de los mensajes MIDI
    new_midi = mido.MidiFile()
    for i, track in enumerate(midi.tracks):
        new_track = mido.MidiTrack()
        current_time = 0
        for msg in track:
            if not msg.is_meta:
                current_time += msg.time
                if msg.type == 'note_on' or msg.type == 'note_off':
                    # Ajustar el tiempo
                    new_time = max(0, msg.time - int(onset_diff * midi.ticks_per_beat))
                    new_track.append(msg.copy(time=new_time))
            else:
                new_track.append(msg)
        new_midi.tracks.append(new_track)
    
    # Guardar el archivo MIDI ajustado
    new_midi.save('adjusted_' + midi_path)