FROM python:latest

WORKDIR /CODE

COPY . .

RUN ["pip", "install"]

CMD ["python3", "src/main.py"]