import paramiko
import time

def cisco_login(hostname, username, password, passw):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False, timeout=10)
        print(f"Terhubung dengan Router {hostname}")
    except Exception as e:
        print(f"Gagal Connect {e}")
        return

    channel = ssh.invoke_shell()
    time.sleep(1)  

    channel.send("enable\n")
    time.sleep(1)  
    channel.send(passw +"\n")
    time.sleep(1)
    output = channel.recv(65535).decode('utf-8')
    print(output)  

    if '#' in output:  
        if hostname == "10.10.10.1":
            time.sleep(1)
            channel.send("configure terminal\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)
            
            channel.send("interface gig0/0\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("ip address 192.168.100.1 255.255.255.0\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("no shutdown\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("exit\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')
            print(output)

            channel.send("ip dhcp pool R1\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("network 192.168.100.0 255.255.255.0\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("default-router 192.168.100.1\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("exit\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')
            print(output)
        elif hostname == "192.168.110.1":
            time.sleep(1)
            channel.send("configure terminal\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)
            
            channel.send("interface gig0/1\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("ip address 10.10.10.2 255.255.255.252\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("no shutdown\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')  
            print(output)

            channel.send("exit\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')
            print(output)

            channel.send("ip route 192.168.100.0 255.255.255.0 10.10.10.1\n")
            time.sleep(1)
            output = channel.recv(65535).decode('utf-8')
            print(output)
        else:
            print("Hostname tidak dikenali")
    else:
        print(f"Gagal masuk mode enable pada {hostname}")

    ssh.close()
    print(f"Konfigurasi pada {hostname} selesai")

if __name__ == "__main__":
    router = [
        {"ip": "192.168.110.1", "username": "admin", "passwd": "Cisco19", "pass": "cisco"},
        {"ip": "10.10.10.1", "username": "admin", "passwd": "Cisco19", "pass": "cisco"}
    ]
    for routers in router:
        cisco_login(routers["ip"], routers["username"], routers["passwd"], routers["pass"])