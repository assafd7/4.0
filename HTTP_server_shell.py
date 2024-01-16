import socket
import os
import logging

# Configure logging
logging.basicConfig(filename='server1.log', level=logging.DEBUG,
                    format="%(asctime)s -- %(lineno)d -- %(levelname)s - %(message)s")

QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
WEB_ROOT = r"C:\Cyber\4.0\WEB-ROOT"
DEFAULT_URL = WEB_ROOT + r"\index.html"
content_types = {
    "html": "text/html; charset=utf-8",
    "jpg": "image/jpeg",
    "css": "text/css",
    "js": "text/javascript; charset=UTF-8",
    "txt": "text/plain",
    "ico": "image/x-icon",
    "gif": "image/gif",
    "png": "image/png"
}
REDIRECTION_DICTIONARY = {"/moved": "/index.html"}


def get_file_data(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
        return file_data
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return f"Error: {e}"


def file_exists_in_folder(file_path):
    return os.path.exists(file_path)


def calculate_content_length(file_path):
    try:
        logging.debug(f"aa {file_path}")
        file_size = os.path.getsize(file_path)
        return file_size
    except Exception as e:
        logging.error(f"Error calculating content length: {e}")
        return None


def cont_type_finder(uri):
    folders_list = uri.split("/")
    folders_list = folders_list[-1].split(".")
    file_extension = folders_list[-1]
    if file_extension in content_types:
        content_type_header = content_types[file_extension]
        return content_type_header
    else:
        return "invalid file extension"


def handle_client_request(resource, client_socket):
    if resource == '' or (resource == "/"):
        uri = DEFAULT_URL
        empty_uri = True
    else:
        uri = resource
        empty_uri = False

    if uri == '/forbidden':
        client_socket.send("HTTP/1.1 403 FORBIDDEN\r\n".encode())
        logging.debug("Sent 403 FORBIDDEN response")
        return
    elif uri in REDIRECTION_DICTIONARY:
        client_socket.send("HTTP/1.1 302 REDIRECTION\r\nlocation: /\r\n".encode())
        logging.debug("Sent 302 REDIRECTION response")
        return
    if uri == "/error":
        client_socket.send("HTTP/1.1 500 INTERNAL SERVER ERROR\r\n".encode())
        logging.debug("Sent 500 INTERNAL SERVER ERROR response")
        return
    else:
        if not empty_uri:
            file_path = WEB_ROOT + uri
            logging.debug(f"a {file_path}")
        else:
            file_path = uri
            logging.debug(f"b {file_path}")

    if not file_exists_in_folder(file_path):
        client_socket.send("HTTP/1.1 400 BAD REQUEST\r\n".encode())
        logging.debug(f"Sent 400 BAD REQUEST response {uri}")
        return

    content_type_header = cont_type_finder(uri)
    content_length_header = calculate_content_length(file_path)
    file_data = get_file_data(file_path)
    response_message = f"HTTP/1.1 200 OK\r\ncontent-type: {content_type_header}\r\nContent-Length: {content_length_header}\r\n\r\n"
    client_socket.send(response_message.encode())
    client_socket.sendall(file_data)
    logging.debug("Sent 200 OK response with file data")


def validate_http_request(request):
    request_parts = request.split(" ")
    logging.debug(f"{request_parts}")
    if len(request_parts) != 3 or request_parts[0] != "GET" or request_parts[2] != "HTTP/1.1\r\n":
        return False, None
    else:
        return True, request_parts[1]


def socket_handle(client_socket):
    try:
        message = ''
        end = ''
        while "\r\n" not in message:
            message += client_socket.recv(1).decode()
        while "\r\n\r\n" not in end:
            end += client_socket.recv(1).decode()

        return message
    except Exception as e:
        logging.error(f"Error handling socket: {e}")
        return f"Error: {e}"


def handle_client(client_socket):
    logging.debug('Client connected')
    while True:
        client_decoded_request = socket_handle(client_socket)
        valid_http, resource = validate_http_request(client_decoded_request)
        logging.debug(f"{valid_http} {resource}")
        if valid_http:
            logging.debug('Got a valid HTTP request')
            handle_client_request(resource, client_socket)
        else:
            client_socket.send("HTTP/1.1 400 BAD REQUEST\r\n".encode())
            logging.debug("Sent 400 BAD REQUEST response")
            break


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        logging.info("Listening for connections on port %d" % PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.debug('New connection received')
                #client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
                logging.debug("passed handle")
            except socket.error as err:
                logging.error('Received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except socket.error as err:
        logging.error('Received socket exception - ' + str(err))
    #except socket.TimeoutError:
        #server_socket.close()
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
