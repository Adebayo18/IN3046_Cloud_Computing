FROM --platform=linux/amd64 python:3.9.18-slim-bullseye

WORKDIR /app

COPY ./sourcecode/flaskProject1 .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host", "0.0.0.0"]