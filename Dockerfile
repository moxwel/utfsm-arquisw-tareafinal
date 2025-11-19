FROM python:3.13-alpine3.22

RUN apk add --no-cache curl

HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=10s CMD curl -f http://localhost:8000/health || exit 1

WORKDIR /code

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

ARG BUILD_DATE=unknown
ENV BUILD_DATE=$BUILD_DATE

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
