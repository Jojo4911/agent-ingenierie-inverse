FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglx-mesa0 libxext6 libsm6 libice6 libxrender1 \
        libfontconfig1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "cadquery>=2.8.0"

COPY run_cadquery.py /opt/run_cadquery.py

RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /work

ENTRYPOINT ["python", "/opt/run_cadquery.py"]
