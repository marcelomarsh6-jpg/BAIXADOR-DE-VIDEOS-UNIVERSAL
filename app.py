import os
import uuid
import time
import threading
import re
from flask import Flask, request, render_template_string, send_file, jsonify
import yt_dlp

app = Flask(__name__)

# Memória volátil para armazenar o status dos downloads
download_tasks = {}

# ==============================================================================
# FRONTEND (VISUAL AZUL CLEAN ORIGINAL + AUTO DOWNLOAD)
# ==============================================================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Downloader Clean Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    
    <style>
        /* --- ESTILO GERAL --- */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
            color: #333; 
            height: 100vh; 
            display: flex; justify-content: center; align-items: center; 
            overflow: hidden;
        }

        /* --- BACKGROUND BLOBS (AZUIS) --- */
        .blob {
            position: absolute; border-radius: 50%; filter: blur(60px); opacity: 0.6; z-index: -1;
            animation: move 10s infinite alternate;
        }
        /* Cores originais Azuis */
        .blob1 { top: -10%; left: -10%; width: 400px; height: 400px; background: #a1c4fd; }
        .blob2 { bottom: -10%; right: -10%; width: 350px; height: 350px; background: #c2e9fb; }

        @keyframes move { from { transform: translate(0, 0); } to { transform: translate(30px, -30px); } }

        /* --- CARTÃO DE VIDRO CLEAN --- */
        .card {
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.9);
            padding: 45px; border-radius: 24px; width: 90%; max-width: 450px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05); text-align: center;
        }
        
        h1 { margin-bottom: 8px; font-weight: 800; font-size: 1.8rem; color: #2d3436; letter-spacing: -0.5px; }
        p.subtitle { color: #636e72; font-size: 0.95rem; margin-bottom: 35px; }

        /* --- INPUTS --- */
        .input-group { margin-bottom: 20px; text-align: left; }
        label { display: block; margin-bottom: 8px; font-size: 0.85rem; color: #2d3436; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        
        input, select { 
            width: 100%; padding: 16px; border: 2px solid #e1e1e1; border-radius: 12px; 
            background: #ffffff; color: #2d3436; font-size: 1rem; font-family: 'Inter', sans-serif;
            outline: none; transition: all 0.2s ease;
        }
        input:focus, select:focus { border-color: #74b9ff; box-shadow: 0 0 0 4px rgba(116, 185, 255, 0.2); }

        /* --- BOTÃO AZUL --- */
        button { 
            width: 100%; padding: 18px; 
            background: linear-gradient(135deg, #0984e3 0%, #74b9ff 100%);
            border: none; color: white; font-weight: 700; border-radius: 12px; cursor: pointer; 
            font-size: 1.05rem; margin-top: 15px; transition: transform 0.2s, box-shadow 0.2s; 
            box-shadow: 0 10px 20px rgba(9, 132, 227, 0.2);
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 15px 25px rgba(9, 132, 227, 0.3); }
        button:disabled { background: #b2bec3; cursor: not-allowed; transform: none; box-shadow: none; }

        /* --- BARRA DE PROGRESSO AZUL --- */
        #progress-area { display: none; margin-top: 30px; text-align: left; }
        
        .progress-track {
            width: 100%; background-color: #e6e6e6; border-radius: 10px; height: 14px; 
            overflow: hidden; margin-top: 10px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .progress-bar {
            height: 100%; width: 0%; 
            background: linear-gradient(90deg, #0984e3, #74b9ff);
            transition: width 0.4s ease; border-radius: 10px;
        }
        
        .status-header { display: flex; justify-content: space-between; align-items: flex-end; }
        .status-text { color: #0984e3; font-weight: 700; font-size: 0.9rem; }
        .percent-text { color: #636e72; font-weight: 600; font-size: 0.85rem; }

    </style>
</head>
<body>

    <div class="blob blob1"></div>
    <div class="blob blob2"></div>

    <div class="card">
        <h1>Baixador Universal</h1>
        <p class="subtitle">Insira o link e escolha a qualidade.</p>
        
        <div id="form-area">
            <div class="input-group">
                <label>Link do Vídeo</label>
                <input type="text" id="url" placeholder="Cole o URL aqui..." autocomplete="off">
            </div>

            <div class="input-group">
                <label>Formato</label>
                <select id="formato" onchange="toggleQuality()">
                    <option value="video">Vídeo MP4</option>
                    <option value="audio">Apenas Áudio (MP3)</option>
                </select>
            </div>

            <div class="input-group" id="div-qualidade-audio" style="display:none;">
                <label>Qualidade do Áudio</label>
                <select id="qualidade_audio">
                    <option value="320">Estúdio (320kbps)</option>
                    <option value="192" selected>Alta (192kbps)</option>
                    <option value="128">Padrão (128kbps)</option>
                </select>
            </div>

            <div class="input-group" id="div-qualidade-video">
                <label>Resolução do Vídeo</label>
                <select id="qualidade_video">
                    <option value="baixa">Baixa (480p - Rápido)</option>
                    <option value="media" selected>Média (720p - HD)</option>
                    <option value="alta">Alta (1080p/4K - Original)</option>
                </select>
            </div>

            <button onclick="startDownload()" id="btn-baixar">Baixar Agora</button>
        </div>

        <div id="progress-area">
            <div class="status-header">
                <span class="status-text" id="status-msg">Iniciando...</span>
                <span class="percent-text" id="percent-txt">0%</span>
            </div>
            <div class="progress-track">
                <div class="progress-bar" id="bar"></div>
            </div>
        </div>

    </div>

    <script>
        function toggleQuality() {
            var val = document.getElementById("formato").value;
            if (val === "audio") {
                document.getElementById("div-qualidade-audio").style.display = "block";
                document.getElementById("div-qualidade-video").style.display = "none";
            } else {
                document.getElementById("div-qualidade-audio").style.display = "none";
                document.getElementById("div-qualidade-video").style.display = "block";
            }
        }
        
        // Inicializa estado
        toggleQuality();

        async function startDownload() {
            const url = document.getElementById('url').value;
            if(!url) return alert("Por favor, cole um link!");
            
            const btn = document.getElementById('btn-baixar');
            btn.disabled = true;
            btn.innerText = "Aguarde...";
            document.getElementById('progress-area').style.display = 'block';
            
            // Reseta UI
            document.getElementById('bar').style.width = "0%";
            document.getElementById('percent-txt').innerText = "0%";

            const formData = new FormData();
            formData.append('url', url);
            formData.append('formato', document.getElementById('formato').value);
            formData.append('qualidade_audio', document.getElementById('qualidade_audio').value);
            formData.append('qualidade_video', document.getElementById('qualidade_video').value);

            try {
                const response = await fetch('/start_task', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.task_id) {
                    trackProgress(data.task_id);
                } else {
                    alert("Erro ao iniciar.");
                    resetUI();
                }
            } catch (e) {
                alert("Erro de conexão.");
                resetUI();
            }
        }

        function trackProgress(taskId) {
            let fakeProgress = 80; // Início da simulação de conversão

            const interval = setInterval(async () => {
                try {
                    const res = await fetch('/status/' + taskId);
                    const data = await res.json();

                    if (data.state === 'error') {
                        clearInterval(interval);
                        alert("Erro: " + data.error);
                        resetUI();
                        return;
                    }

                    // --- LÓGICA INTELIGENTE DA BARRA ---
                    let percent = data.percent || 0;
                    
                    // Se estiver convertendo (backend travado em 80%), simula progresso
                    if (data.state === 'converting') {
                         if (fakeProgress < 95) fakeProgress += 0.5;
                         percent = fakeProgress;
                    }

                    document.getElementById('bar').style.width = percent + "%";
                    document.getElementById('percent-txt').innerText = parseInt(percent) + "%";
                    document.getElementById('status-msg').innerText = data.status_msg;

                    if (data.state === 'finished') {
                        clearInterval(interval);
                        
                        // Atualiza visualmente para 100%
                        document.getElementById('bar').style.width = "100%";
                        document.getElementById('percent-txt').innerText = "100%";
                        document.getElementById('status-msg').innerText = "Download Iniciado!";
                        
                        // Habilita o botão (caso o download automático falhe)
                        document.getElementById('btn-baixar').innerText = "Salvar Arquivo";
                        document.getElementById('btn-baixar').disabled = false;
                        document.getElementById('btn-baixar').onclick = function() {
                            window.location.href = "/get_file/" + data.filename;
                        };

                        // --- AQUI ESTÁ A MÁGICA: DOWNLOAD AUTOMÁTICO ---
                        window.location.href = "/get_file/" + data.filename;
                        
                        // Recarrega a página após 4 segundos para limpar tudo
                        setTimeout(() => location.reload(), 4000);
                    }
                } catch (e) { console.log(e); }
            }, 800);
        }

        function resetUI() {
            document.getElementById('btn-baixar').disabled = false;
            document.getElementById('btn-baixar').innerText = "Baixar Agora";
            document.getElementById('progress-area').style.display = 'none';
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# BACKEND (PYTHON / FLASK / YT-DLP)
# ==============================================================================

def run_download_thread(task_id, url, formato, q_audio, q_video, base_dir, ffmpeg_path):
    download_folder = os.path.join(base_dir, "downloads")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    def my_progress_hook(d):
        if d['status'] == 'downloading':
            # Tenta calcular porcentagem real
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            
            if total:
                real_percent = (downloaded / total) * 100
                # Download vale 80% da barra, conversão vale os outros 20%
                ui_percent = real_percent * 0.80 
                
                download_tasks[task_id]['percent'] = ui_percent
                download_tasks[task_id]['status_msg'] = f"Baixando... {int(real_percent)}%"
            
        elif d['status'] == 'finished':
            download_tasks[task_id]['percent'] = 80
            download_tasks[task_id]['state'] = 'converting'
            download_tasks[task_id]['status_msg'] = "Processando..."

   # OPÇÕES (CONFIGURAÇÃO DO NOME DO ARQUIVO)
    ydl_opts = {
        'outtmpl': f'{download_folder}/- BAIXADOR - UNIVERSAL - %(title)s.%(ext)s',
        'noplaylist': True,
        'overwrites': True,
        
        # FALSE PARA MANTER ESPAÇOS E ACENTOS NO NOME
        'restrictfilenames': False, 
        
        # --- REMOVA A LINHA 'ffmpeg_location' QUE ESTAVA AQUI ---
        # O Docker já instalou o FFmpeg no sistema, o yt-dlp vai achar sozinho.

        'progress_hooks': [my_progress_hook],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    # SELEÇÃO DE QUALIDADE
    if formato == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': q_audio,
            }],
        })
    else:
        # Lógica de Vídeo
        if q_video == 'baixa':
            fmt = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        elif q_video == 'media':
            fmt = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        else:
            fmt = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        ydl_opts.update({
            'format': fmt,
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            final_filename = filename
            if formato == 'audio':
                final_filename = filename.rsplit('.', 1)[0] + '.mp3'
            else:
                base = filename.rsplit('.', 1)[0]
                if os.path.exists(base + '.mp4'): final_filename = base + '.mp4'
                elif os.path.exists(base + '.mkv'): final_filename = base + '.mkv'

            download_tasks[task_id]['filename'] = os.path.basename(final_filename)
            download_tasks[task_id]['percent'] = 100
            download_tasks[task_id]['state'] = 'finished'

    except Exception as e:
        download_tasks[task_id]['state'] = 'error'
        download_tasks[task_id]['error'] = str(e)

# --- ROTAS ---

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/start_task', methods=['POST'])
def start_task():
    task_id = str(uuid.uuid4())
    url = request.form.get('url')
    formato = request.form.get('formato')
    q_audio = request.form.get('qualidade_audio', '192')
    q_video = request.form.get('qualidade_video', 'media')
    
    download_tasks[task_id] = {
        'state': 'processing', 'percent': 0, 
        'status_msg': 'Conectando...', 'filename': None
    }
    
    base_dir = os.getcwd()
    thread = threading.Thread(
        target=run_download_thread, 
        args=(task_id, url, formato, q_audio, q_video, base_dir, base_dir)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def status(task_id):
    task = download_tasks.get(task_id)
    if task: return jsonify(task)
    return jsonify({'state': 'error', 'error': 'Task not found'})

@app.route('/get_file/<filename>')
def get_file(filename):
    try:
        return send_file(os.path.join(os.getcwd(), "downloads", filename), as_attachment=True)
    except Exception as e: return str(e)

# AJUSTE PARA O SERVIDOR LINUX (RENDER)
if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    # O Render fornece a porta pela variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    
    # host='0.0.0.0' é obrigatório para servidores web

    app.run(host='0.0.0.0', port=port)
