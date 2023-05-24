import socket
import threading
import json
import uuid
from enum import Enum
from datetime import datetime
from transfer import Request, Response, Notification
from server_classes import User, Resource, Reservation, ReservationStatus
from server_classes import ReservationQuantityOverflow, ReservationOverlapError

HOST = 'localhost'
PORT = 5556
BUFFER_SIZE = 20480
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
    return None

def get_reservation_by_id(reservation_id):
    for resource in Resources:
        for r in resource.get_reservation_list().get_all():
            if r.id == reservation_id:
                return r, resource
    return None
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
            errors = []
            resource_id = None
            start = None
            quantity = None
            duration = None
            try:
                resource_id = int(params[1])
            except ValueError:
                errors.append("Resource id must be an integer.")
            try:
                quantity = int(params[2])
                if quantity < 1:
                    raise ValueError()
            except ValueError:
                errors.append("Quantity must be a positive integer greater than 0.")
            try:
                start = datetime.strptime(" ".join(params[3:5]), "%d/%m/%Y %H:%M")
            except ValueError:
                errors.append("Invalid start time format. Please use format: dd/mm/yyyy HH:MM")
            try:
                duration = int(params[5])
                if duration < 1:
                    raise ValueError()
            except ValueError:
                errors.append("Duration must be a positive integer greater than 0.")

            resource = get_resource_by_id(resource_id)
            if resource is None:
                errors.append("Resource ID is incorrect.")

            if len(errors) == 0:

                reservation = Reservation(resource_id=resource_id,
                                          user_name=user.name,
                                          reserved_quantity=quantity,
                                          start_time=start,
                                          duration=duration)
                try:
                    resource.get_reservation_list().add(reservation)
                    reservation_json = reservation.to_dict()
                    response = Response(message=f'Success: {reservation_json["reserved_quantity"]} '
                                                f'{resource.get_unit_measure()} blocked for '
                                                f'{reservation_json["duration"]} minutes starting at '
                                                f'{reservation_json["start_time"]}')
                    notify_all_users(f'{user.name} blocked {quantity} {resource.get_unit_measure()} of '
                                     f'{resource.get_name()} starting at {" ".join(params[3:5])} '
                                     f'for {duration} minutes',
                                     username_to_exclude=user.name)
                except ReservationQuantityOverflow as e:
                    response = Response(message=str(e))
                except ReservationOverlapError as e:
                    response = Response(message=str(e))


            else:
                response = Response(message='ERRORS: \n' + "\n".join(errors))
    elif request.get_command() == 'cancel':
        params = request.get_params()
        if len(params) > 0:
            errors = []
            user_name = params[0]
            try:
                id = uuid.UUID(params[1])
            except ValueError:
                errors.append("Id is not valid.")
            if len(errors) > 0:
                response = Response(message='ERRORS: \n' + "\n".join(errors))
            else:
                reservation, resource = get_reservation_by_id(id)
                if reservation is None:
                    response = Response(message=f'Reservation id is not valid!')
                else:
                    if reservation.user_name != user_name:
                        response = Response(message=f'ERROR: Only {reservation.user_name} is allowed cancel its reservation.')
                    else:
                        resource.get_reservation_list().remove(reservation)
                        response = Response(message=f'SUCCESS: Reservation {id} cancelled!')
                        notify_all_users(f'{user_name} cancelled its reservation',
                                 username_to_exclude=user_name)

        else:
            response = Response(message=f'ERROR: You must specify an id.')
    elif request.get_command() == 'update':
        params = request.get_params()
        if len(params) > 0:
            errors = []
            user_name = params[0]
            try:
                id = uuid.UUID(params[1])
            except ValueError:
                errors.append("Id is not valid.")
            try:
                start = datetime.strptime(" ".join(params[2:4]), "%d/%m/%Y %H:%M")
            except ValueError:
                errors.append("Invalid start time format. Please use format: dd/mm/yyyy HH:MM")
            try:
                duration = int(params[4])
                if duration < 1:
                    raise ValueError()
            except ValueError:
                errors.append("Duration must be a positive integer greater than 0.")
            if len(errors) > 0:
                response = Response(message='ERRORS: \n' + "\n".join(errors))
            else:
                reservation, resource = get_reservation_by_id(id)
                if reservation is None:
                    response = Response(message=f'ERROR: Reservation id is not valid!')
                else:
                    if reservation.user_name != user_name:
                        response = Response(
                            message=f'ERROR: Only {reservation.user_name} is allowed update its reservation.')
                    else:
                        resource.get_reservation_list().remove(reservation)
                        reservation.start_time = start
                        reservation.duration = duration
                        resource.get_reservation_list().add(reservation)
                        response = Response(message=f'SUCCESS: Reservation {id} updated! It starts at {start} with a duration of {duration} minutes')
                        notify_all_users(f'{user_name} updated its reservation',
                                         username_to_exclude=user_name)
    elif request.get_command() == 'finish':
        pass
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
