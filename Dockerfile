# syntax=docker/dockerfile:1
#
# Local smoke-test container for the Golden Target reconciliation tool.
#
# Build:
#   docker build -t golden-target-tool .
# Run against a pack:
#   docker run --rm -v $(pwd)/golden-target-data/exam:/pack golden-target-tool python3 solve.py /pack

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3-pip \
        ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python3.11"]
CMD ["solve.py", "/pack"]
