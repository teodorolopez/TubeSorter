FROM python:3.14-alpine

ENV TZ=UTC
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ENV INTERVAL=24
ENV SECRETS_DIR=/app/secrets
ENV CONFIG_DIR=/app/config

RUN mkdir -p ${SECRETS_DIR} ${CONFIG_DIR}

ADD https://api.github.com/repos/teodorolopez/TubeSorter/git/refs/heads/main /tmp/version.json

RUN apk --no-cache add git && \
    git clone --depth 1 https://github.com/teodorolopez/TubeSorter.git /tmp/repo && \
    mv /tmp/repo/tube-sorter.py /app/ && \
    mv /tmp/repo/requirements.txt /app/ && \
    rm -rf /tmp/repo /tmp/version.json && \
    apk del git

RUN pip install --no-cache-dir -r /app/requirements.txt

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD pgrep -f "tube-sorter.py" || exit 1

CMD ["python", "tube-sorter.py"]