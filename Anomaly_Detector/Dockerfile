FROM ubuntu:22.04
LABEL maintainer="kmillar10@my.bcit.ca"
WORKDIR /app
RUN apt-get update -y
RUN apt-get install -y python3 python3-pip
COPY ./requirements.txt /app/requirements.txt
RUN python3 -m pip install -r requirements.txt
COPY . .
ENTRYPOINT ["python3"]
CMD ["app.py"]
