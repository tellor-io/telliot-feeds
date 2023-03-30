FROM python:3.9

RUN pip install telliot-feeds==0.1.8

CMD echo "telliot image built"
