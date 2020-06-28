FROM ubuntu:18.04
RUN apt-get update && apt-get install -y redis-server && apt-get clean
EXPOSE 6379
CMD ["redis-server", "--bind 0.0.0.0", "--protected-mode no", "--slaveof redis-l 6379"]

#to run:
#docker build --tag redis-follower .
#docker run --name redis-f -d -p 6379:6378 redis-follower
