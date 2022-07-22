FROM python:3.9.13-slim-bullseye

COPY ./bot/requirements.txt ./

RUN apt-get -y update && \
    pip install -r requirements.txt --no-cache-dir && \
    apt-get -y autoremove

COPY ./bot/scheduler.py ./bot/solaire_helpers.py ./bot/solaire.py /src/

WORKDIR /src

CMD ["python", "solaire.py"]