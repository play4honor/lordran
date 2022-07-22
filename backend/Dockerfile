FROM python:3.9.13-slim-bullseye

COPY ./requirements.txt ./

RUN apt-get -y update && \
    pip install -r requirements.txt --no-cache-dir && \
    apt-get -y autoremove

COPY quelaag.py queries.py form_helpers.py /src/

WORKDIR /src
RUN mkdir db

EXPOSE 3838

CMD ["python", "quelaag.py"]