import socket
import base64
import mimetypes
import ssl
import os
import sys

HOST = 'smtp.yandex.ru'
PORT = 465
BOUNDARY = '--this_is_my_boundary'


def send_command(sock, command, buffer=1024 * 9):
    sock.send(command + b'\n')
    return sock.recv(buffer).decode()


def extract_files(directory):
    for filename in os.listdir(directory):
        yield filename


def get_config():
    with open('config.txt', 'r', encoding='utf8') as config:
        name = config.readline().split('=')[1].rstrip()
        recipients = config.readline().split('=')[1].rstrip()
        topic = config.readline().split('=')[1].rstrip()
        recipients = recipients.replace(" ", "").split(',')
        return name, recipients, topic


def handle_attachments(files):
    result_attachments = []
    for file in files:
        type, extention = mimetypes.guess_type(file)
        file = './attachments/' + file
        with open(file, 'rb') as f:
            encoded_file = base64.b64encode(f.read())
            mime_type = type
            result_attachments.append(
                (f'Content-Disposition: attachment; '
                 f'\nfilename="{file}"\n'
                 f'Content-Transfer-Encoding: base64\n'
                 f'Content-Type: {mime_type};\n name="{file}"\n\n') \
                + encoded_file.decode())

    return f'\n--{BOUNDARY}\n'.join(result_attachments)


def create_message(name, recipients, theme, message_text, attachments):
    recipient = ','.join(recipients)
    return (
        f'From: {name}\n'
        f'To: {recipient}\n'
        f'MIME-Version: 1.0\n'
        f'Subject: {theme}\n'
        f'Content-Type: multipart/mixed;\n boundary="{BOUNDARY}"\n\n'
        f'--{BOUNDARY}\n'
        f'Content-Transfer-Encoding: 8bit\n'
        f'Content-Type: text/plain; charset=utf-8\n\n'
        f'{message_text}\n'
        f'--{BOUNDARY}\n'
        f'{attachments}'
        f'\n--{BOUNDARY}--\n'
        f'.'
    )


def prepare_message_text(text_filename):
    with open(text_filename, 'r', encoding='utf-8') as f:
        result = ''
        lines = f.readlines()
        for line in lines:
            if line[0] == '.':
                line = '.' + line
            result += line
    return result


def send_message(login, password):
    name, recipients, theme = get_config()
    print(recipients, theme)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock = ssl.wrap_socket(sock)
        sock.connect((HOST, PORT))
        print(sock.recv(1024).decode())
        print(send_command(sock, b'EHLO test'))
        print(send_command(sock, b'AUTH LOGIN'))
        print(send_command(sock, base64.b64encode(login.encode())))
        print(send_command(sock, base64.b64encode(password.encode())))
        print(send_command(sock, b'MAIL FROM:' + login.encode()))
        for recipient in recipients:
            print(send_command(sock, b'RCPT TO: ' + recipient.encode()))
        print(send_command(sock, b'DATA'))
        prepared_message = prepare_message_text('message.txt')
        attachments = handle_attachments(extract_files('./attachments'))
        message = create_message(name, recipients, theme, prepared_message, attachments)
        print(send_command(sock, message.encode()))


if __name__ == '__main__':
    print('LOGIN:')
    login = input()
    print('PASSWORD:')
    password = input()
    send_message(login, password)
