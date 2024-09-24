from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import moviepy.editor as mp
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
TRANSLATED_FOLDER = 'translated'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TRANSLATED_FOLDER'] = TRANSLATED_FOLDER

# Ensure directories exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(TRANSLATED_FOLDER):
    os.makedirs(TRANSLATED_FOLDER)

def extract_audio(video_file, output_audio_file):
    clip = mp.VideoFileClip(video_file)
    clip.audio.write_audiofile(output_audio_file)

def convert_audio_to_text(audio_file, language='en-IN'):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)  
        text = recognizer.recognize_google(audio_data, language=language)
        return text

def translate_text(text, target_language):
    translated = GoogleTranslator(source='auto', target=target_language).translate(text)
    return translated

def convert_text_to_speech(text, output_audio_file, target_language):
    tts = gTTS(text=text, lang=target_language, slow=False)
    tts.save(output_audio_file)

def combine_audio_with_video(video_file, audio_file, output_video_file):
    video_clip = mp.VideoFileClip(video_file)
    audio_clip = mp.AudioFileClip(audio_file)
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(output_video_file, codec='libx264', audio_codec='aac')

def translate_video(video_file, target_language):
    output_audio_file = 'audio.wav'
    output_translated_audio_file = 'translated_audio.wav'
    output_video_file = os.path.join(app.config['TRANSLATED_FOLDER'], 'translated_video.mp4')

    # Extract audio from video
    extract_audio(video_file, output_audio_file)

    # Convert audio to text
    text = convert_audio_to_text(output_audio_file)

    # Translate text
    translated_text = translate_text(text, target_language)

    # Convert translated text to speech
    convert_text_to_speech(translated_text, output_translated_audio_file, target_language)

    # Combine translated audio with original video
    combine_audio_with_video(video_file, output_translated_audio_file, output_video_file)

    # Clean up temporary audio files
    os.remove(output_audio_file)
    os.remove(output_translated_audio_file)

    return output_video_file

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error="No file chosen")
        
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error="No file chosen")
        
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        target_language = request.form['language']
        translated_video_file = translate_video(filename, target_language)
        
        translated_video_filename = os.path.basename(translated_video_file)
        
        return render_template('index.html', result=translated_video_filename)
    
    return render_template('index.html')

@app.route('/translated/<filename>')
def translated_file(filename):
    return send_from_directory(app.config['TRANSLATED_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
