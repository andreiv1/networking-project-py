import socket
import threading
import json
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

def receive_response(server):
    while True:
        data = server.recv(BUFFER_SIZE).decode('utf-8')
        try:
            data_json = json.dumps(data)
            if "type" in data_json:
                print(data_json)
        except Exception as e:
            print(str(e))
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((HOST, PORT))
        receive_thread = threading.Thread(target=receive_response,args=(server_socket,))
        receive_thread.start()
        user_input = input('Username: ')
        send_request(server_socket, Request(command="auth", params=user_input))
        while user_input.strip() != 'exit':
            user_input = input('>')
            tokens = user_input.strip().split()
            if tokens[0] == 'help':
                help_menu()
            elif tokens[0] == 'list_resources':
                print("List resources:")
                send_request(server_socket, Request(command="list_resources"))
            elif tokens[0] == 'block':
                if len(tokens) < 6:
                    print("Usage: block <resourceID> <resourceQuantity> <startDate> <startHour> <duration>")
                else:
                    print("to send request")
                    pass

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