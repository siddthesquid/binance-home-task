FROM python:3.6

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY README.md ./
COPY sidd ./sidd

CMD ["gunicorn", "-b", "0.0.0.0:8000", "server:app", "-w", "1", "--threads", "8"]
