# Usa uma imagem leve do Python
FROM python:3.9-slim

# Instala FFmpeg e GIT (O Git agora é obrigatório para baixar a atualização)
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
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
