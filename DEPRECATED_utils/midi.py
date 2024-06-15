import mido
import numpy as np

def nota_a_frequencia(nota):
    """Convert MIDI note number to frequency in Hz."""

    return 440.0 * (2.0 ** ((nota - 69) / 12.0))


def nota_a_cifrado(nota):
    """Convert MIDI note number to note name."""

    notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octava = nota // 12 - 1
    cifrado = notas_base[nota % 12]
    return f"{cifrado}{octava}"


def analizar_archivo(path):
    """Analyze a single MIDI file to find the lowest and highest notes."""

    midi = mido.MidiFile(path)
    nota_liminf = float('inf')
    nota_limsup = float('-inf')

    for track in midi.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                nota = msg.note
                if nota < nota_liminf:
                    nota_liminf = nota
                if nota > nota_limsup:
                    nota_limsup = nota

    freq_liminf = nota_a_frequencia(nota_liminf)
    freq_limsup = nota_a_frequencia(nota_limsup)
    cifrado_liming = nota_a_cifrado(nota_liminf)
    cifrado_limsup = nota_a_cifrado(nota_limsup)
    
    return nota_liminf, nota_limsup, freq_liminf, freq_limsup, cifrado_liming, cifrado_limsup
