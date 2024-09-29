FROM ultralytics/ultralytics:8.2.99
# FROM ultralytics/ultralytics:8.2.99-python # Does not include CUDA, that is why it is so big

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

COPY . .

CMD [ "python", "app.py" ]