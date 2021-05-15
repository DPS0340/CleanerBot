FROM python:latest

WORKDIR /CODE

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "src/main.py"]