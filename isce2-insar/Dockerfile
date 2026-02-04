FROM isce/isce2:latest

RUN apt update && \
    apt install -y git curl zip unzip nano

ENV ISCE_HOME=/usr/lib/python3.8/dist-packages/isce/
ENV PATH=$ISCE_HOME/applications:$PATH