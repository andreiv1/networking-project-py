import socket
import threading
from transfer import Request, Response

HOST = 'localhost'
PORT = 5556
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

def send_request(server, request):
    server.sendall(str(request).encode('utf-8'))
    data = server.recv(BUFFER_SIZE).decode('utf-8')
    response = Response.from_json(data)
    return response

def receive_notifications(server):
    while True:
        try:
            data = server.recv(BUFFER_SIZE).decode('utf-8')
            if not data:
                break
            response = Response.from_json(data)
            print("Received notification: {}".format(str(response)))
        except Exception as e:
            print("Error receiving notification:", str(e))
            break
# Commands
def auth(server, user_name):
    response = send_request(server, Request(command="auth", params=user_name))
    print(str(response))

def list_resources(server):
    response = send_request(server, Request(command="list_resources"))
    print(str(response))
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((HOST, PORT))
        user_input = input('Username: ')
        auth(server_socket, user_input)
        notification_thread = threading.Thread(target=receive_notifications, args=(server_socket,))
        notification_thread.start()
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