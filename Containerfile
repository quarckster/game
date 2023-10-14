FROM docker.io/library/debian:12-slim as builder

RUN apt-get update && \
    apt-get install -y python3 python3-venv python3-pip

COPY requirements.txt /requirements.txt

RUN python3 -m venv /app_venv

ENV PATH=/app_venv/bin:${PATH}

RUN pip3 install -U pip wheel && \
    pip3 install -r /requirements.txt

FROM docker.io/library/debian:12-slim

RUN apt-get update && \
    apt-get install -y python3 ca-certificates && \
    apt-get clean

COPY --from=builder /app_venv /app_venv

COPY app/ /app

RUN chmod -R a+rwX /app_venv /app

ENV PATH=/app_venv/bin:${PATH}

EXPOSE 8080

WORKDIR /app

USER 1001

CMD ["/app/main.py"]
