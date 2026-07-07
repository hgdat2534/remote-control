import os
import struct

# Chỉ định 1 thư mục duy nhất được phép thao tác (Sandbox)
# Nó sẽ tự tạo thư mục tên "Client_Shared_Data" ở cùng nơi để code
SHARED_FOLDER = os.path.abspath("./Client_Shared_Data")
if not os.path.exists(SHARED_FOLDER):
    os.makedirs(SHARED_FOLDER)

def is_safe_path(filename):
    """Hàm kiểm tra an toàn: Chặn người dùng gõ '../' để hack ra ngoài"""
    # Xóa các khoảng trắng thừa hoặc ký tự nguy hiểm cơ bản
    clean_name = os.path.basename(filename) 
    target_path = os.path.abspath(os.path.join(SHARED_FOLDER, clean_name))
    return target_path.startswith(SHARED_FOLDER)

def get_file_list():
    """Trả về danh sách các file đang có trong thư mục dưới dạng chuỗi"""
    try:
        files = os.listdir(SHARED_FOLDER)
        if not files:
            return "Thư mục đang trống."
        return "\n".join(files)
    except Exception as e:
        return f"Lỗi khi đọc thư mục: {e}"

def delete_file(filename):
    """Xóa file an toàn"""
    if not is_safe_path(filename):
        return "Lỗi: Truy cập bị từ chối (Vượt quá thư mục cho phép)!"
    
    filepath = os.path.join(SHARED_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return f"Đã xóa thành công file: {filename}"
    else:
        return f"Lỗi: Không tìm thấy file {filename}."

def get_file_info_for_download(filename):
    """Kiểm tra an toàn và trả về (đường_dẫn, dung_lượng_file)"""
    if not is_safe_path(filename):
        return None 
        
    filepath = os.path.join(SHARED_FOLDER, filename)
    if not os.path.exists(filepath):
        return None
        
    # Lấy dung lượng file thực tế (tính bằng bytes)
    file_size = os.path.getsize(filepath)
    return filepath, file_size
