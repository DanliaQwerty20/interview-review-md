FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY interview_review ./interview_review
COPY app.py ./

RUN pip install --no-cache-dir .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]

