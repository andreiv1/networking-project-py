import socket
import threading
import uuid
from enum import Enum
from datetime import timedelta
from datetime import timedelta

import socket


class User:
    def __init__(self, name, client_socket):
        self._name = name
        self._client_socket = client_socket

    def send_message(self, message):
        if self._client_socket is not None and isinstance(self._client_socket, socket.socket):
            try:
                self._client_socket.sendall(message.encode('utf-8'))
            except:
                pass
        else:
            self._client_socket = None

    @property
    def client_socket(self):
        return self._client_socket

    @client_socket.setter
    def client_socket(self, new_socket):
        self._client_socket = new_socket

    @property
    def name(self):
        return self._name


class ReservationQuantityOverflow(Exception):
    pass

class ReservationOverlapError(Exception):
    pass
class ResourceReservationList:
    def __init__(self, maximum_capacity):
        self.reservations = []
        self.maximum_capacity = maximum_capacity
        self.lock = threading.Lock()

    def add(self, reservation):
        with self.lock:
            total_reserved_quantity = sum(r.get_quantity() for r in self.reservations
                                          if
                                          r.start_time < reservation.end_time and r.end_time > reservation.start_time)

            if total_reserved_quantity + reservation.get_quantity() > self.maximum_capacity:
                raise ReservationQuantityOverflow(f'The capacity tried to block ({reservation.get_quantity()}) '
                                                  f'is not possible.\n'
                                                  f'Resource capacity: {self.maximum_capacity}')

            self.reservations.append(reservation)

    def remove(self, reservation):
        with self.lock:
            self.reservations.remove(reservation)
            self.capacity -= reservation.get_quantity()
            if self.capacity < 0:
                self.capacity = 0

    def get_all(self):
        with self.lock:
            return self.reservations[:]


class Resource:
    def __init__(self, resource_id, name, maximum_capacity, unit_measure):
        self.resource_id = resource_id
        self.name = name
        self.maximum_capacity = maximum_capacity
        self.unit_measure = unit_measure
        self.reservation_list = ResourceReservationList(maximum_capacity)

    def get_available_capacity(self, start_time, end_time):
        pass

    def get_reservation_list(self):
        return self.reservation_list

    def get_unit_measure(self):
        return self.unit_measure

    def get_name(self):
        return self.name

    def to_dict(self):
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "maximum_capacity": self.maximum_capacity,
            "unit_measure": self.unit_measure,
            "reservations": [reservation.to_dict() for reservation in self.reservation_list.reservations]
        }


class ReservationStatus(Enum):
    BLOCKED = 1
    RESERVED = 2


class Reservation:
    def __init__(self, resource_id, user_name, reserved_quantity, start_time, duration,
                 status=ReservationStatus.BLOCKED):
        self.id = uuid.uuid4()
        self.resource_id = resource_id
        self.user_name = user_name
        self.reserved_quantity = reserved_quantity
        self.start_time = start_time
        self.duration = duration  # in minutes
        self.status = status

    def get_status(self):
        return self.status

    def get_quantity(self):
        return self.reserved_quantity

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration)

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_name": self.user_name,
            "reserved_quantity": self.reserved_quantity,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status.name
        }
