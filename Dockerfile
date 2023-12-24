FROM python:3.9

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
COPY HHCIODriver.py /usr/local/bin/HHCIODriver.py
COPY main.py /usr/local/bin/main.py

CMD ["python3", "/usr/local/bin/main.py"]