FROM python:3.12-slim

WORKDIR /app
COPY crossfield crossfield
COPY data data
COPY site site
RUN python -m crossfield build

EXPOSE 8000
CMD ["python", "-m", "crossfield", "serve", "--host", "0.0.0.0", "--port", "8000"]
