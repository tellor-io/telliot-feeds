FROM python:3.9

RUN pip install telliot-feeds

CMD ["pip", "freeze"]