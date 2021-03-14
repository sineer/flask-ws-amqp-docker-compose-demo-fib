FROM python:3.6
RUN mkdir /app/
COPY . /app/
WORKDIR /app/
EXPOSE 5000
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
