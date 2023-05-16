from tabulate import tabulate
import socket
import json
from datetime import datetime
from transfer import Request, Response

HOST = 'localhost'
PORT = 4449
BUFFER_SIZE = 1024


def help_menu():
    print("==================   COMMANDS: ===================================")
    print("** list_resources -> this shows the resources")
    print("** list_reservations -> this shows my resource reservation")
    print("** block <resourceID> <resourceQuantity> <startDate> <startHour> <endDate> <endHour>")
    print("** cancel <reservationID>")
    print("** update <reservationID> <startDate> <startHour> <endDate> <endHour>")
    print("** finish <reservationID> -> only for blocked resources")
    print("==================================================================")

def send_command(server, command, param=None):
    request = Request(command=command, params=param)
    server.sendall(str(request).encode('utf-8'))
    data = server.recv(BUFFER_SIZE).decode('utf-8')
    response = Response.from_json(data)
    return response

def auth(server, user):
    response = send_command(server, "auth", user)
    list_resources(server)

def list_resources(server):
    response = send_command(server, "list_resources")
    # print(str(response))

    # print(str(resources))
    headers = ["ID", "Resource", "Capacity", "Unit Measure", "Reservations"]
    table_data = []
    for resource in response.get_message():
        reservations = resource["reservations"]
        reservation_table_data = [[r["reservation_id"],r["user"],r["quantity"],r["start_date"], r["end_date"]] for r in reservations]
        resource_table_data = [resource["resource_id"], resource["name"], resource["maximum_capacity"], resource["unit_measure"],
                               tabulate(reservation_table_data, headers=["Reservation ID", "User", "Quantity", "Start Date",
                                                                         "Duration", "End Date"])]
        table_data.append(resource_table_data)
    print(tabulate(table_data, headers=headers))

def block(server, params):
    response = send_command(server, 'block', params)
    print(response.get_message())

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((HOST, PORT))
        user_input = input('Username: ')
        auth(server_socket, user_input)
        while user_input.strip() != 'exit':
            user_input = input('>')
            tokens = user_input.strip().split()
            if tokens[0] == 'help':
                help_menu()
            elif tokens[0] == 'list_resources':
                print("List resources:")
                list_resources(server_socket)
            elif tokens[0] == 'block':
                if len(tokens) < 6:
                    print("Usage: block <resourceID> <resourceQuantity> <startDate> <startHour> <duration>")
                else:
                    block(server_socket, tokens[1:])
                    # try:
                    #     start_date = datetime.strptime(" ".join(tokens[3:5]), "%d/%m/%Y %H:%M")
                    #
                    # except:
                    #     print("Wrong date format, expected: day/month/year hour:minute")

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


if __name__ == '__main__':
    main()
