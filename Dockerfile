FROM python:3.9

RUN pip3 install paho-mqtt
COPY HHCIODriver.py /usr/local/bin/HHCIODriver.py
COPY main.py /usr/local/bin/main.py

CMD ["python3", "/usr/local/bin/main.py"]