# Usa uma imagem leve do Python
FROM python:3.9-slim

# Instala o FFmpeg (ESSENCIAL para o yt-dlp funcionar em HD)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Define a pasta de trabalho
WORKDIR /app

# Copia os arquivos do projeto para o servidor
COPY . /app

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Cria a pasta de downloads para garantir que existe
RUN mkdir -p downloads

# Comando para iniciar o app
CMD ["python", "app.py"]