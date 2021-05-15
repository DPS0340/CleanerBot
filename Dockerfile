FROM python:latest

WORKDIR /CODE

COPY . .

RUN pip install -r requirements.txt

CMD ["python3", "src/main.py"]