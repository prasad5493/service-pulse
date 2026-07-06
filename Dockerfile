# Runs the health checks once inside a container.
# Handy for local testing and a consistent environment anywhere.
#
#   docker build -t service-pulse .
#   docker run --rm service-pulse

FROM python:3.11-slim

# Never run as root, even in a throwaway container.
RUN useradd --create-home pulse
WORKDIR /home/pulse

# Copy requirements first so this layer is cached between code changes.
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

USER pulse

CMD ["python", "-m", "checks"]
