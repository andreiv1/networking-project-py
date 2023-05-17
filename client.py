import socket
import threading
import json
import os
import sys
from transfer import Request, Response, Notification
from tabulate import tabulate

HOST = 'localhost'
PORT = 5556
BUFFER_SIZE = 1024

is_running = True


class TerminateMainThreadException(Exception):
    pass


def help_menu():
    print("==================   COMMANDS: ===================================")
    print("** list_resources -> this shows the resources")
    print("** list_reservations -> this shows my resource reservation")
    print("** block <resourceID> <resourceQuantity> <startDate> <startHour> <durationInMinutes>")
    print("** cancel <reservationID>")
    print("** update <reservationID> <startDate> <startHour> <endDate> <endHour>")
    print("** finish <reservationID> -> only for blocked resources")
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

        try:
            data_json = json.loads(data)
            # print(data_json)
            if "type" in data_json:
                # print(data_json["type"])
                if data_json["type"] == "response":
                    show_response(Response.from_json(data))
                elif data_json["type"] == "notification":
                    show_notification(Notification.from_json(data))
        except Exception as e:
            print(str(e))


def show_response(response):
    if isinstance(response, Response):
        message = response.get_message()
        if "resources" in message:
            print("====================  RESOURCES ==================== ")
            resources = message["resources"]
            headers = ["ID", "Resource", "Capacity", "Unit Measure", "Reservations"]
            table_data = []
            for resource in resources:
                reservations = resource["reservations"]
                reservation_table_data = [
                    [r["reservation_id"], r["user"], r["quantity"], r["start_date"], r["end_date"]] for r in
                    reservations]
                resource_table_data = [resource["resource_id"], resource["name"], resource["maximum_capacity"],
                                       resource["unit_measure"],
                                       tabulate(reservation_table_data,
                                                headers=["Reservation ID", "User", "Quantity", "Start Date",
                                                         "Duration", "End Date"])]
                table_data.append(resource_table_data)
            print(tabulate(table_data, headers=headers))
        else:
            print(message)


def show_notification(notification):
    if isinstance(notification, Notification):
        print("Notification:", notification.get_message())
        if notification.get_action() is not None:
            if notification.get_action() == "exit":
                raise TerminateMainThreadException()

username = None
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((HOST, PORT))
        try:
            receive_thread = threading.Thread(target=receive_response, args=(server_socket,))
            receive_thread.start()
            user_input = input('Username: ')
            username = user_input
            send_request(server_socket, Request(command="auth", params=username))
            send_request(server_socket, Request(command="list_resources"))
            while user_input.strip() != 'exit':
                user_input = input()
                tokens = user_input.strip().split()
                if len(tokens) > 0:
                    if tokens[0] == 'help':
                        help_menu()
                    elif tokens[0] == 'list_resources':
                        send_request(server_socket, Request(command="list_resources"))
                    elif tokens[0] == 'block':
                        if len(tokens) < 6:
                            print("Usage: block <resourceID> <resourceQuantity> <startDate> <startHour> "
                                  "<durationInMinutes>")
                        else:
                            params = [username]
                            params[1:] = tokens[1:]
                            send_request(server_socket, Request(command="block", params=params))

                    elif tokens[0] == 'cancel':
                        if len(tokens) < 2:
                            print("Usage: cancel <reservationID>")
                    elif tokens[0] == 'update':
                        if len(tokens) < 7:
                            print("Usage: update <reservationID> <startDate> <startHour> <endDate> <endHour>")

                    elif tokens[0] == 'finish':
                        if len(tokens) < 2:
                            print("Usage: finish <reservationID>")
                    elif user_input != 'exit':
                        print("Unknown command, write 'help' to view commands.")
        except TerminateMainThreadException:
            sys.exit()
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
