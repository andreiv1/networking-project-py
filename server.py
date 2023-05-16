import socket
import threading
import uuid
import json
from enum import Enum
from datetime import datetime

HOST = 'localhost'
PORT = 4123
BUFFER_SIZE = 1024

users = []


class User:
    def __init__(self, name, client_socket):
        self.name = name
        self._client_socket = client_socket

    def send_message(self, message):
        self._client_socket.sendall(message.encode('utf-8'))

    @property
    def client_socket(self):
        return self._client_socket

    @client_socket.setter
    def client_socket(self, new_socket):
        self._client_socket = new_socket


def get_user_by_name(name):
    matched_users = [user for user in users if user.name == name]
    return matched_users[0] if matched_users else None

class ReservationList:
    def __init__(self):
        self.reservations = []
        self.lock = threading.Lock()

    def add_reservation(self, reservation):
        with self.lock:
            self.reservations.append(reservation)

    def remove_reservation(self, reservation):
        with self.lock:
            self.reservations.remove(reservation)

    def get_reservations(self):
        with self.lock:
            return self.reservations[:]
class Resource:
    def __init__(self, resource_id, name, maximum_capacity, unit_measure):
        self.resource_id = resource_id
        self.name = name
        self.maximum_capacity = maximum_capacity
        self.unit_measure = unit_measure
        self.reservation_list = ReservationList()

    def get_available_capacity(self, start_time, end_time):
        pass

    def to_dict(self):
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "maximum_capacity": self.maximum_capacity,
            "unit_measure": self.unit_measure,
            "reservations": self.reservation_list.get_reservations()
        }


Resources = tuple([Resource(1, "CPU", 16, "cores"),
                   Resource(2, "RAM", 32, "GB"),
                   Resource(3, "Storage", 128, "GB")])

def get_resource_by_id(resource_id):
    for resource in Resources:
        if resource.resource_id == resource_id:
            return resource
class ReservationStatus(Enum):
    BLOCKED = 1
    RESERVED = 2


class Reservation:
    def __init__(self, resource_id, user_name, start_time, end_time):
        self.id = uuid.uuid4()
        self.resource_id = resource_id
        self.user_name = user_name
        self.start_time = start_time
        self.end_time = end_time
        self.status = ReservationStatus.BLOCKED


is_running = True


def handle_client(client):
    with client:
        while True:
            if client is None:
                break

            data = client.recv(BUFFER_SIZE)
            if not data:
                break
            try:
                json_data = json.loads(data.decode('utf-8'))
                print(json_data)
                command = json_data['command']
                param = json_data['param']

                # AUTH
                if command == 'auth':
                    client_name = param

                    user = get_user_by_name(client_name)

                    if user is None:
                        users.append(User(client_name, client))
                        response = {"message": f'User {client_name} registered!'}
                    else:
                        response = {"message": f'Welcome back, {client_name}!'}
                        user.client_socket.close()
                        user.client_socket = client

                    client.sendall(json.dumps(response).encode('utf-8'))
                # LIST
                elif command == 'list_resources':
                    resources = [resource.to_dict() for resource in Resources]
                    response = json.dumps(resources).encode('utf-8')
                    client.sendall(response)
                elif command == 'block':
                    print(param)
                    resource_id = param[0]
                    resource_quantity = param[1]

                    fullStartDate = datetime.strptime(" ".join(param[2:4]), "%d/%m/%Y %H:%M")
                    fullEndDate = datetime.strptime(" ".join(param[4:6]), "%d/%m/%Y %H:%M")

                    response = {"message": f"Resource for interval {fullStartDate} - {fullEndDate} blocked."}
                    client.sendall(json.dumps(response).encode('utf-8'))
                elif True:
                    response = {"message": "Command " + command + " not found!"}
                    client.sendall(json.dumps(response).encode('utf-8'))
            except json.decoder.JSONDecodeError:
                break

def accept(server):
    while is_running:
        client, addr = server.accept()
        print(f'{addr} has connected')
        client_thread = threading.Thread(target=handle_client, args=(client,))
        client_thread.start()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        print(f'Server listening on {HOST}:{PORT}')
        server.listen()
        accept_thread = threading.Thread(target=accept, args=(server,))
        accept_thread.start()
        accept_thread.join()


if __name__ == '__main__':
    main()
