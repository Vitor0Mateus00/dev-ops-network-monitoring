FROM python:3.12.3

WORKDIR /api

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "api.v1.main:app", "--port", "8000", "--host", "0.0.0.0"]