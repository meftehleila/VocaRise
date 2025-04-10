// js/script.js

// Éléments DOM
const dropZone = document.getElementById('drop-zone');
const audioUpload = document.getElementById('audio-upload');
const audioPreview = document.getElementById('audio-preview');
const textStep = document.getElementById('text-step');
const generateBtn = document.getElementById('generate-btn');
const loadingMessage = document.getElementById('loading-message');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const resultContainer = document.getElementById('result-container');
const resultAudio = document.getElementById('result-audio');
const downloadBtn = document.getElementById('download-btn');
const textInput = document.getElementById('text-input');
const loadingPopup = document.getElementById('loading-popup');

// Variables
let audioBlob = null;
let selectedAudioFile = null;

// 🔹 Cacher la section résultat au chargement
resultContainer.classList.add('hidden'); // ✅ Toujours masqué au chargement

// 🔹 Masquer le résultat si texte modifié
textInput.addEventListener('input', () => {
  resultContainer.classList.add('hidden');
});

// 🔹 Masquer le résultat si audio changé
audioUpload.addEventListener('change', (e) => {
  resultContainer.classList.add('hidden');
  if (e.target.files.length) {
    handleAudioFile(e.target.files[0]);
  }
});

// 🔹 Upload via clic sur zone
dropZone.addEventListener('click', () => audioUpload.click());

// 🔹 Drag & Drop
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('active');
});

['dragleave', 'dragend'].forEach(type => {
  dropZone.addEventListener(type, () => {
    dropZone.classList.remove('active');
  });
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('active');
  if (e.dataTransfer.files.length) {
    handleAudioFile(e.dataTransfer.files[0]);
    resultContainer.classList.add('hidden');
  }
});

// 🔹 Traitement du fichier audio
function handleAudioFile(file) {
  selectedAudioFile = file; // ✅ Stockage global
  if (!file.type.match('audio.*')) {
    showError('Veuillez sélectionner un fichier audio valide');
    return;
  }

  audioBlob = URL.createObjectURL(file);
  audioPreview.src = audioBlob;
  audioPreview.classList.remove('hidden');

  dropZone.innerHTML = `
    <div style="text-align: left;">
      <p style="color: var(--success); margin-bottom: 0.5rem;">✓ Fichier prêt</p>
      <p style="font-weight: 500;">${file.name}</p>
      <p style="opacity: 0.7; font-size: 0.9rem;">${(file.size / (1024 * 1024)).toFixed(1)} MB</p>
    </div>
  `;
  dropZone.appendChild(audioPreview);
  textStep.style.display = 'block';
}

// 🔹 Génération de la voix clonée
generateBtn.addEventListener('click', async () => {
  const text = textInput.value.trim();
  const audioFile = selectedAudioFile;

  if (!text) {
    showError('Veuillez entrer un texte à prononcer');
    return;
  }

  if (!audioFile) {
    showError('Veuillez importer un fichier audio');
    return;
  }

  generateBtn.disabled = true;
  progressContainer.classList.remove('hidden');
  progressBar.style.width = '0%';

  const formData = new FormData();
  formData.append('audio', audioFile);
  formData.append('text', text);

  try {
    loadingPopup.classList.remove('hidden');
    const response = await fetch('/api/clone-voice', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) throw new Error('Erreur lors de la génération');

    const result = await response.json();

    if (result.success && result.audio_url) {
      resultAudio.src = result.audio_url;
      resultAudio.load();
      resultContainer.classList.remove('hidden');

      downloadBtn.onclick = () => {
        const a = document.createElement('a');
        a.href = result.audio_url;
        a.download = 'voix-clonee.mp3';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      };

      resultContainer.scrollIntoView({ behavior: 'smooth' });
    } else {
      showError("Erreur : aucune réponse audio reçue.");
    }
  } catch (error) {
    showError(error.message);
  } finally {
    generateBtn.disabled = false;
    progressContainer.classList.add('hidden');
    loadingPopup.classList.add('hidden');
  }
});

// 🔹 Barre de progression (facultative)
function simulateProgress() {
  let width = 0;
  const interval = setInterval(() => {
    if (width >= 100) {
      clearInterval(interval);
    } else {
      width += Math.random() * 15;
      progressBar.style.width = Math.min(width, 100) + '%';
    }
  }, 300);
}

// 🔹 Notification d'erreur simple
function showError(message) {
  alert(message);
}
