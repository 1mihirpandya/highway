FROM python:3.6
WORKDIR /gatekeeper/src/app
COPY Gatekeeper.py .
COPY Constants.py .
RUN pip install requests flask flask_restful
EXPOSE 5000
CMD [ "python", "Gatekeeper.py" ]

#to run:
#docker build --tag gatekeeper .
#docker run -d -p 5000:5000 gatekeeper
