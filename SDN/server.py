import os
import asyncio
from flask import Flask, request, jsonify
import socket
import socket
import json
import psutil

app = Flask(__name__)

#konfigurasi socket
UDP_IP = "10.0.1.1" #ganti dengan IP controller anda
UDP_port = 6633
data_lama = {}

#fungsi untuk membuat nama file unik
def make_unique_filename(directory, filename):
    base, extension = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    
    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base} ({counter}){extension}"
        counter += 1
    return unique_filename

#Endpoint untuk menerima file via POST request
@app.route('/upload', methods=['POST'])
def upload_file():
    #pastikan ada data dalam body
    if not request.files:
       return jsonify({"error": "No file uploaded in request"}), 400
    
    #Ambil file yang diunggah dari request.files
    uploaded_file = request.files['file']
    
    #periksa apakah file diunggah dengan benar
    if uploaded_file.filename =='':
        return jsonify({"error": "No selected file"}), 400
    # Tentukan nama file default
    filename = uploaded_file.filename
    directory = '/home/mininet/coba'
    os.makedirs(directory, exist_ok=True) #buat direktory jika belum ada
    
    #Buat nama file unik jika file dengan nama yang sama sudah ada
    unique_filename = make_unique_filename(directory, filename)
    filepath = os.path.join(directory, unique_filename)
    
    #simpan data dari file yang diunggah ke file
    try:
        uploaded_file.save(filepath)
    except Exception as e:
        return jsonify({"error": f"Failed to sace file:{e}"}), 500
    return jsonify({"message": f"File saved as {unique_filename}"}), 200

@app.route('/')
def index():
    #(Optional) Anda dapat mengimplementasikan logika yang sesuai disini
    return 'Hello, World'

#fungsi untuk mengirim data ke kontroller
async def send_data_to_controller():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        data = {'CPU': cpu_usage, 'MEMORY': memory_usage, 'DISK': disk_usage}
        
        if data != data_lama:
           try:
               sock.sendto(json.dumps(data).encode(), (UDP_IP, UDP_PORT))
               print(f"Data terkirim: {data}")
               data_lama.update(data)
           except Exception as e:
               print(f"Gagal mengirim data: {e}")
        
        else:
            print("Data sama")
        await asyncio.sleep(5)
        
#Menjalankan FLask dan tugas asynchronous
def run_flask():
    app.run(host="0.0.0.0", port=80)

async def main():
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, run_flask)
    await send_data_to_controller()

if __name__ == '__main__':
    asyncio.run(main())
