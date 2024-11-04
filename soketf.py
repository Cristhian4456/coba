import asyncio
from flask import Flask
import socket
import json
import psutil

app = Flask(__name__)

# Konfigurasi socket
UDP_IP = "10.0.1.1"  # Ganti dengan IP controller Anda
UDP_PORT = 6633
data_lama = {}

async def send_data_to_controller():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        # Mengambil data sumber daya
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        # Membentuk data dalam format JSON
        data = {
            'CPU': cpu_usage,
            'MEMORY': memory_usage,
            'DISK': disk_usage
        }

        # Mengirim data ke controller
        if data != data_lama:
            try:
                sock.sendto(json.dumps(data).encode(), (UDP_IP, UDP_PORT))
                print(f"Data terkirim: {data}")
                data_lama.update(data)
            except Exception as e:
                print(f"Gagal mengirim data: {e}")
        else:
            print("Data sama")
        
        # Jeda sebelum pengiriman berikutnya
        await asyncio.sleep(5)

@app.route('/')
def index():
    return 'Hello, World!'

def run_flask():
    # Menjalankan Flask di thread terpisah
    app.run(host="0.0.0.0", port=80)

async def main():
    # Jalankan Flask di thread terpisah
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, run_flask)

    # Jalankan tugas asynchronous untuk mengirim data ke controller
    await send_data_to_controller()

if __name__ == '__main__':
    asyncio.run(main())
