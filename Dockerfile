FROM python:slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

CMD ["python3", "main.py"]