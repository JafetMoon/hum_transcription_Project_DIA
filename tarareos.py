import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display

def process_audio_files(folder_path, L):

    sample_rate = 22050
    n_fft = int((L * sample_rate) / 1000)
    hop_length = int(n_fft / 4)

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

def save_spectrogram(file_path, spectrogram_db, sr, hop_length):

    plt.figure(figsize=(10, 6))
    librosa.display.specshow(spectrogram_db, sr=sr, hop_length=hop_length, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'Espectrograma de STFT de {os.path.basename(file_path)}')
    
    # Save the figure
    output_filename = os.path.splitext(file_path)[0] + '_spectrogram.png'
    plt.savefig(output_filename)
    plt.close()


