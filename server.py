import socket
import threading
import json
from enum import Enum
from datetime import datetime
from transfer import Request, Response, Notification
from server_classes import User, Resource, Reservation, ReservationStatus

HOST = 'localhost'
PORT = 5556
BUFFER_SIZE = 1024
is_running = True

users = []
def get_user_by_name(name):
    matched_users = [user for user in users if user.name == name]
    return matched_users[0] if matched_users else None


def notify_all_users(message, username_to_exclude=None, action=None):
    notified_users = 0
    notification = Notification(message, action)
    for user in users:
        if username_to_exclude is not None:
            if user.name != username_to_exclude:
                user.send_message(str(notification))
                notified_users += 1
        else:
            user.send_message(str(notification))
            notified_users += 1
    print(f'Notified {notified_users} users with: {message}')


def notify_user(user, message, action=None):
    notification = Notification(message, action)
    user.send_message(str(notification))
    print(f'Notified user {user.name} with: {message}, action=', str(action))

Resources = tuple([Resource(1, "CPU", 16, "cores"),
                   Resource(2, "RAM", 32, "GB"),
                   Resource(3, "Storage", 128, "GB")])


def get_resource_by_id(resource_id):
    for resource in Resources:
        if resource.resource_id == resource_id:
            return resource
def process_request(request, client):
    print(str(request))
    # AUTH
    if request.get_command() == 'auth':
        client_name = request.get_params()
        user = get_user_by_name(client_name)
        new_user = False
        if user is None:
            user = User(client_name, client)
            users.append(user)
            new_user = True
            response = Response(message=f'Your user "{client_name}" is now registered!')
        else:
            response = Response(message=f'Welcome back, {user.name}!')
            notify_user(user, message="Another client started a session, you will be disconnected.", action="exit")
            user.client_socket.close()
            user.client_socket = client

        if new_user:
            notify_all_users(f'User {client_name} registered!', username_to_exclude=client_name)
        else:
            notify_all_users(f'User {client_name} is online.', username_to_exclude=client_name)
    # LIST
    elif request.get_command() == 'list_resources':
        resources = {"resources": [resource.to_dict() for resource in Resources]}
        response = Response(message=resources)
    elif request.get_command() == 'block':
        params = request.get_params()
        user = get_user_by_name(params[0])
        if user is None:
            response = Response(message="Couldn't block the resource.")
        else:
            resource_id = int(params[1])
            quantity = int(params[2])
            start = datetime.strptime(" ".join(params[3:5]), "%d/%m/%Y %H:%M")
            duration = int(params[5])

            resource = get_resource_by_id(resource_id)
            reservation = Reservation(resource_id=resource_id,
                                      user_name=user.name,
                                      reserved_quantity=quantity,
                                      start_time=start,
                                      duration=duration)
            resource.get_reservation_list().add(reservation)
            reservation_json = reservation.to_dict()
            response = Response(message=reservation_json)
            notify_all_users(f'{user.name} blocked {quantity} {resource.get_unit_measure()} of '
                             f'{resource.get_name()} starting at {" ".join(params[3:5])} '
                             f'for {duration} minutes',
                             username_to_exclude=user.name)
    elif True:
        response = Response(message=f"Command {command} not found!")

    return response


def handle_client(client):
    with client:
        while True:
            if client is None:
                break
            try:
                data = client.recv(BUFFER_SIZE)
                if not data:
                    break
            except:
                break
            try:
                request = Request.from_json(data.decode('utf-8'))
                response = process_request(request, client)
                client.sendall(str(response).encode('utf-8'))
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
