FROM python:3.6
RUN mkdir /app
WORKDIR /app
COPY Gatekeeper.py /app/
COPY Constants.py /app/
RUN pip install requests flask flask_restful redis
EXPOSE 5000
CMD [ "python", "/app/Gatekeeper.py" ]

#to run:
#docker build --tag gatekeeper .
#docker run -d -p 5000:5000 gatekeeper
