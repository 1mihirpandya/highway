FROM ubuntu:18.04
RUN apt-get update && apt-get install -y redis-server && apt-get clean
EXPOSE 6379

#to run:
#docker build --tag redis-leader .
#docker run -d -p 6379:6379 redis-leader
