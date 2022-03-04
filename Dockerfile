FROM python:3.7
WORKDIR /app
COPY requirements.txt .
RUN apt-get -y update &&\
    apt-get -y upgrade &&\
    apt-get install --allow git &&\
    apt-get clean

RUN apt-get -y install libspatialindex-dev
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8086
COPY . .
CMD [ "gunicorn", "--bind", "0.0.0.0:8086", "main:app" ]