#!python3

import socket
from threading import Lock
import logging


class HHCIODriver(object):
    def __init__(self, host, port, on_connect_event=None, on_disconnect_event=None):
        self.host = host
        self.port = port
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.on_connect_event = on_connect_event
        self.on_disconnect_event = on_disconnect_event
        self.socket_lock = Lock()

    def is_connected(self):
        return self.connected

    def get_hostname(self):
        return self.host

    def get_port(self):
        return self.port

    def _on_socket_connect(self):
        logging.info("Device is now connected.")

        self.connected = True
        if self.on_connect_event is not None:
            self.on_connect_event()

    def _on_socket_disconnect(self):
        logging.info("Device is now disconnected.")

        self.connected = False
        if self.on_disconnect_event is not None:
            self.on_disconnect_event()

    def connect(self, skip=False):
        logging.debug("Trying to open a socket connection")

        try:
            with self.socket_lock:
                if not self.connected:
                    try:
                        #try to close it in case it thinks it is open
                        self.socket.close()
                    except:
                        pass
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.settimeout(5)
                    self.socket.connect((self.host,self.port))
                else:
                    return True
        except socket.error as e:
            logging.critical("Failed to connect to the device: {}".format(e))
            if not skip:
                self._on_socket_disconnect()
            return False

        self._on_socket_connect()

        logging.debug("Connect operation completed")

        return True

    def disconnect(self, skip=False):
        if not self.connected:
            return

        self.socket.close()
        if not skip:
            self._on_socket_disconnect()

    def operate_relay(self, relay, state):
        if not self.connected:
            raise ConnectionError("Driver is not connected!")
        if relay <= 0 or relay > 8:
            raise ValueError("Invalid relay number specified!")

        if state:
            message = 'on{}'.format(relay)
        else:
            message = 'off{}'.format(relay)

        logging.debug("Sending socket message: {}".format(message))

        try:
            with self.socket_lock:
                self.socket.send(message.encode())
                self.socket.recv(5)
        except socket.error as e:
            logging.critical("Failed to send command to the device: {}".format(e))
            self._on_socket_disconnect()
            raise ConnectionError("Driver is not connected!")

    def read_outputs(self):
        if not self.connected:
            raise ConnectionError("Driver is not connected!")

        try:
            with self.socket_lock:
                self.socket.send('read'.encode())
                data = self.socket.recv(13).decode()
                bits = data[5:] # length of returned string "relay"
                # Return bits in reverse order because the relay controller
                # returns them in a way that the last bit is the first relay
                return bits[::-1]

        except socket.error as e:
            logging.critical("Failed to send command \"read\" to the device: {}".format(e))
            self._on_socket_disconnect()
            raise ConnectionError("Driver is not connected!")

    def read_input(self, input):
        if not self.connected:
            raise ConnectionError("Driver is not connected!")
        if input <= 0 or input > 8:
            raise ValueError("Invalid input number specified!")


        try:
            with self.socket_lock:
                self.socket.send('input'.encode())
                data = self.socket.recv(15).decode()

            position = 4+input

            return data[-1 * input]
        except socket.error as e:
            logging.critical("Failed to send command to the device: {}".format(e))
            self._on_socket_disconnect()
            raise ConnectionError("Driver is not connected!")

