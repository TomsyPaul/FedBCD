FROM ubuntu:18.04
RUN apt update
RUN apt install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt update
RUN apt install -y python3.7 python3-pip
#RUN python3.7 -m pip install tensorflow==1.13.1
#RUN python3.7 -m pip install typing-extensions wheel
CMD /bin/bash
