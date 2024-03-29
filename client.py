import socket
import threading
import json
import os
import sys
from transfer import Request, Response, Notification
from tabulate import tabulate

HOST = 'localhost'
PORT = 5556
BUFFER_SIZE = 20480

is_running = True


class TerminateMainThreadException(Exception):
    pass


def help_menu():
    print("==================   COMMANDS: ===================================")
    print("** list -> shows the table with resources and its reservation")
    print("** block <resourceID> <resourceQuantity> <dd/mm/yyyy> <HH:MM> <minutes>")
    print("** cancel <reservationID>")
    print("** update <reservationID> <dd/mm/yyyy> <HH:MM> <minutes>")
    print("** finish <reservationID>")
    print("==================================================================")


def send_request(server, request):
    server.sendall(str(request).encode('utf-8'))


def receive_response(server):
    while True:
        try:
            data = server.recv(BUFFER_SIZE).decode('utf-8')
        except ConnectionResetError:
            print("Connection to the server closed")
            break
        # print(data)
        try:
            data_json = json.loads(data)
            if "type" in data_json:
                # print(data_json["type"])
                if data_json["type"] == "response":
                    show_response(Response.from_json(data))
                elif data_json["type"] == "notification":
                    show_notification(Notification.from_json(data))

        except Exception as e:
            print(f'Error receiving data from server.')
            break


def show_response(response):
    if isinstance(response, Response):
        message = response.get_message()
        if "resources" in message:
            print("========================================  RESOURCES ======================================== ")
            resources = message["resources"]
            # print(resources)

            resource_headers = ["ID", "Resource", "Max Capacity", "Unit Measure", "", ""]
            resource_table = []

            reservations_headers = ["Reserv ID", "Username", "Quantity", "Start Time", "Duration", "Status"]

            for resource in resources:
                resource_row = [
                    resource["resource_id"], resource["name"],
                    resource["maximum_capacity"], resource["unit_measure"]
                ]
                resource_table.append(resource_row)
                reservations_table = []
                reservations = resource["reservations"]

                if len(reservations) > 0:
                    resource_table.append(["Reservations:"])
                    resource_table.append(reservations_headers)
                    for r in reservations:
                        reservation_row = [
                            r["id"], r["user_name"], r["reserved_quantity"], r["start_time"], r["duration"], r["status"]
                        ]
                        reservations_table.append(reservation_row)

                    resource_table.extend(reservations_table)

                    resource_table.append([])
                else:
                    resource_table.append(["No reservations."])
                    resource_table.append([])

            print(tabulate(resource_table, headers=resource_headers))

        else:
            print(message)


def show_notification(notification):
    if isinstance(notification, Notification):
        print("Notification:", notification.get_message())
        if notification.get_action() is not None:
            if notification.get_action() == "exit":
                raise TerminateMainThreadException()


user_name = None


def main():
    global user_name
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((HOST, PORT))
        try:
            receive_thread = threading.Thread(target=receive_response, args=(server_socket,))
            receive_thread.start()
            user_input = input('Username: ')
            user_name = user_input
            send_request(server_socket, Request(command="auth", params=user_name))
            send_request(server_socket, Request(command="list_resources"))
            while user_input.strip() != 'exit':
                user_input = input()
                tokens = user_input.strip().split()
                params = [user_name]

                if len(tokens) > 0:
                    params[1:] = tokens[1:]
                    if tokens[0] == 'help':
                        help_menu()
                    elif tokens[0] == 'list':
                        send_request(server_socket, Request(command="list_resources"))
                    elif tokens[0] == 'block':
                        if len(tokens) < 6:
                            print("Usage: block <resourceID> <resourceQuantity> <dd/mm/yyyy> <HH:MM> <minutes>")
                        else:
                            send_request(server_socket, Request(command="block", params=params))

                    elif tokens[0] == 'cancel':
                        if len(tokens) < 2:
                            print("Usage: cancel <reservationID>")
                        else:
                            send_request(server_socket, Request(command="cancel", params=params))
                    elif tokens[0] == 'update':
                        if len(tokens) < 5:
                            print("Usage: update <reservationID> <dd/mm/yyyy> <HH:MM> <minutes>")
                        else:
                            send_request(server_socket, Request(command="update",params=params))
                    elif tokens[0] == 'finish':
                        if len(tokens) < 2:
                            print("Usage: finish <reservationID>")
                        else:
                            send_request(server_socket, Request(command="finish", params=params))
                    elif user_input != 'exit':
                        print("Unknown command, write 'help' to view commands.")
        except TerminateMainThreadException:
            sys.exit()


if __name__ == '__main__':
    main()
