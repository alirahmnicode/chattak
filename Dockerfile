FROM docker.arvancloud.ir/python:alpine3.19
WORKDIR /app
COPY . .
RUN python -m venv env
RUN source env/bin/activate
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8000"]