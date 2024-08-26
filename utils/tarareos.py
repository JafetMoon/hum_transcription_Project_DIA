import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display

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


##### 4 
def extract_audio_onsets(audio_path):
    # Cargar el archivo de audio
    y, sr = librosa.load(audio_path)
    
    # Detección de onsets
    onset_times = librosa.onset.onset_detect(y=y, sr=sr, backtrack=False, units='time')
    
    return onset_times


# Función para ajustar el desfase entre audio y MIDI usando el onset
def align_midi_to_audio(midi_path, audio_onsets, threshold=0.05):
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