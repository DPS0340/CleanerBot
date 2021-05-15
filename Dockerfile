FROM python:latest

WORKDIR /CODE

COPY . .

CMD ["python3", "src/main.py"]