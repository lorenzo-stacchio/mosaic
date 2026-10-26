FROM python:3.12-slim

WORKDIR /app
COPY mosaic mosaic
COPY data data
COPY site site
RUN python -m mosaic build

EXPOSE 8000
CMD ["python", "-m", "mosaic", "serve", "--host", "0.0.0.0", "--port", "8000"]
