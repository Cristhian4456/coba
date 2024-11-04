import socket
import json
import psutil
import time
import SimpleHTTPServer
import SocketServer
import threading

# Konfigurasi alamat controller (alamat IP dan port controller yang akan menerima UDP)
CONTROLLER_IP = "10.0.1.1"  # Sesuaikan dengan alamat IP controller
CONTROLLER_PORT = 6633  # Port UDP controller untuk menerima resource info 
def get_resource_info():
    """Mengambil informasi resource (CPU, MEMORY, DISK) dari sistem server."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory().percent
    disk_info = psutil.disk_usage('/').percent

    resource_data = {
        'CPU': cpu_usage,
        'MEMORY': memory_info,
        'DISK': disk_info
    }
    
    return resource_data

def send_resource_info():
    """Mengirim informasi resource ke controller melalui UDP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Membuat socket UDP
    controller_address = (CONTROLLER_IP, CONTROLLER_PORT)
    kirim = 10
    waktu_awal = 0
    last_time = time.time()
    while True:
        resource_data = get_resource_info()
        resource_json = json.dumps(resource_data)  # Konversi resource menjadi format JSON
        try:
            if waktu_awal == 0 or time.time() - last_time >= kirim:
                sock.sendto(resource_json.encode('utf-8'), controller_address)
                print("Resource info sent: {resource_data}")
                waktu_awal += 1
                last_time = time.time()
        except Exception as e:
            print("Failed to send resource info: {e}")
        
        
def run_http_server():
    PORT = 80
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", PORT), Handler)
    print("HTTP Server berjalan pada port", PORT)
    httpd.serve_forever()


if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server)
    http_thread.daemon = True
    http_thread.start()
    
    send_resource_info()
    
    
