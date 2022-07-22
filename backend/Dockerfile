FROM python:3.9.13-slim-bullseye

COPY ./backend/requirements.txt ./

RUN apt-get -y update && \
    pip install -r requirements.txt --no-cache-dir && \
    apt-get -y autoremove

COPY ./backend/quelaag.py ./backend/queries.py ./backend/form_helpers.py /src/

WORKDIR /src
RUN mkdir db

EXPOSE 3838

CMD ["python", "quelaag.py"]