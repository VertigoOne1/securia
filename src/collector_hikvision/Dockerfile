FROM python:3.12.4-alpine3.20

RUN apk update && apk add python3-dev \
                        gcc \
                        libffi-dev \
                        musl-dev

RUN apk add librdkafka-dev --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community

WORKDIR /

COPY . .

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./app.py" ]