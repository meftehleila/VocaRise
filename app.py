import os
import traceback
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pydub import AudioSegment

# --- Configurations ---
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

app = Flask(__name__, static_folder='frontend', static_url_path='')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 🔁 TTS sera chargé plus tard
tts = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/clone-voice', methods=['POST'])
def clone_voice():
    global tts
    try:
        if 'audio' not in request.files or 'text' not in request.form:
            return jsonify({'error': 'Fichier audio ou texte manquant'}), 400

        file = request.files['audio']
        text = request.form['text']

        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Format de fichier non autorisé'}), 400

        # Chargement du modèle TTS à la première requête uniquement
        if tts is None:
            print("🔁 Chargement du modèle YourTTS...")
            from TTS.api import TTS as TTSModel
            tts = TTSModel(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)
            print("✅ Modèle TTS chargé")

        # 🔐 Générer des noms uniques
        ext = os.path.splitext(file.filename)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upload_{timestamp}{ext}"
        wav_filename = f"converted_{timestamp}.wav"
        output_name = f"voice_clone_{timestamp}.mp3"

        # 📥 Sauvegarde du fichier original
        raw_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(raw_path)

        # 🎧 Conversion en wav mono 16kHz
        wav_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
        audio = AudioSegment.from_file(raw_path).set_channels(1).set_frame_rate(16000).normalize()
        audio.export(wav_path, format="wav")

        # 🧠 Synthèse vocale avec TTS
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_name)
        tts.tts_to_file(
            text=text.strip() + ".",
            speaker_wav=wav_path,
            language="fr-fr",
            temperature=0.1,
            speed=0.9,
            file_path=output_path
        )

        # ⏳ Silence final pour plus de naturel
        final_audio = AudioSegment.from_file(output_path)
        final_audio += AudioSegment.silent(duration=1500)
        final_audio.export(output_path, format="mp3")

        return jsonify({'success': True, 'audio_url': f'/api/audio/{output_name}'})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur : {str(e)}'}), 500

@app.route('/api/audio/<filename>')
def get_audio(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ Flask running on port {port}")
    app.run(host='0.0.0.0', port=port)
