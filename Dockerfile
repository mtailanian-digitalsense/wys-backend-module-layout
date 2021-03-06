FROM python:3.7
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8086
COPY . .
CMD [ "gunicorn", "--bind", "0.0.0.0:8086", "main:app" ]
