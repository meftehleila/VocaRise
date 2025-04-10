import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from TTS.api import TTS
import uuid
from datetime import datetime

# Configuration
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

app = Flask(
    __name__,
    static_folder='frontend',
    static_url_path=''
)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Charger le modèle YourTTS
tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/clone-voice', methods=['POST'])
def clone_voice():
    try:
        if 'audio' not in request.files or 'text' not in request.form:
            return jsonify({'error': 'Fichier audio ou texte manquant'}), 400

        file = request.files['audio']
        text = request.form['text']

        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Format de fichier non autorisé'}), 400

        # 🔐 Générer un nom unique pour le fichier
        ext = os.path.splitext(file.filename)[1]
        unique_name = uuid.uuid4().hex
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"upload_{timestamp}{ext}"
        wav_filename = f"wav_user_upload_{timestamp}.wav"
        output_name = f"voice_clone_{timestamp}.mp3"

        # 📥 Enregistrer le fichier audio uploadé
        raw_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(raw_path)
        print("Fichier reçu et enregistré :", raw_path)

        # 🎧 Convertir en WAV mono 16kHz
        wav_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
        audio = AudioSegment.from_file(raw_path).set_channels(1).set_frame_rate(16000).normalize()
        audio.export(wav_path, format="wav")
        print("Audio converti en WAV :", wav_path)

        # 🧠 Générer l'audio cloné
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_name)
        print("Génération de la voix...")

        tts.tts_to_file(
            text=text.strip() + ".",
            speaker_wav=wav_path,
            language="fr-fr",
            temperature=0.1,
            speed=0.9,
            speaker_embedding=None,
            file_path=output_path
        )

        # ⏳ Ajouter silence pour plus de naturel
        final_audio = AudioSegment.from_file(output_path)
        final_audio += AudioSegment.silent(duration=1500)
        final_audio.export(output_path, format="mp3")
        print("Fichier final généré :", output_path)

        return jsonify({
            'success': True,
            'audio_url': f'/api/audio/{output_name}'
        })

    except Exception as e:
        print("ERREUR LORS DE LA GÉNÉRATION :", str(e))
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur : {str(e)}'}), 500


@app.route('/api/audio/<filename>')
def get_audio(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
