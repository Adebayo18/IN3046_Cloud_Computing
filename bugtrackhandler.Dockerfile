FROM --platform=linux/amd64 python:3.9.18-slim-bullseye

WORKDIR /app

COPY ./sourcecode/handler .

RUN pip install -r requirements.txt

EXPOSE 5001

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5001"]