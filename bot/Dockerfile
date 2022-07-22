FROM python:3.9.13-slim-bullseye

COPY ./requirements.txt ./

RUN apt-get -y update && \
    pip install -r requirements.txt --no-cache-dir && \
    apt-get -y autoremove

COPY scheduler.py solaire_helpers.py solaire.py /src/

WORKDIR /src

EXPOSE 3838

CMD ["python", "solaire.py"]