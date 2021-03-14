FROM python:3.6

WORKDIR /app
EXPOSE 5001
ADD requirements.txt ./
RUN pip install -r requirements.txt
ADD ./app.py ./
CMD python app.py
