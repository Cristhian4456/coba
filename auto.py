import paramiko


def cisco_login(hostname, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname, username=username, password=password, allow_agent=False, look_for_keys=False)
        print("Terhubung dengan Router", hostname)
    except Exception as e:
        print("Gagal Connect")
        
    channel = ssh.invoke_shell()
    channel.send("enable\n")
    output = channel.recv(65535).decode('utf-8')
    
    if '#' in output:
        if hostname == "192.168.10.1":
            channel.send("configure terminal\n")
            channel.send("interface gig0/0\n")
            channel.send("ip address 192.168.100.1 255.255.255.0\n")
            channel.send("no shutdown\n")
            channel.send("exit\n")
            channel.send("interface gig0/1\n")
            channel.send("ip address 10.10.10.1 255.255.255.252\n")
            channel.send("no shutdown\n")
            channel.send("exit\n")
            channel.send("ip dhcp pool R1\n")
            channel.send("network 192.168.100.0 255.255.255.0\n")
            channel.send("default-router 192.168.100.1\n")
            channel.send("exit\n")
            channel.send("ip route 192.168.110.0 255.255.255.0 10.10.10.2\n")
            ssh.close()
        elif hostname == "192.168.20.1":
            channel.send("configure terminal\n")
            channel.send("interface gig0/0\n")
            channel.send("ip address 192.168.110.1 255.255.255.0\n")
            channel.send("no shutdown\n")
            channel.send("exit\n")
            channel.send("interface gig0/1\n")
            channel.send("ip address 10.10.10.2 255.255.255.252\n")
            channel.send("no shutdown\n")
            channel.send("exit\n")
            channel.send("ip dhcp pool R2\n")
            channel.send("network 192.168.110.0 255.255.255.0\n")
            channel.send("default-router 192.168.110.1\n")
            channel.send("exit\n")
            channel.send("ip route 192.168.110.0 255.255.255.0 10.10.10.2\n")
            ssh.close()
        else:
            print("No connection")
if __name__ == "main":
    router = [
        {"ip": "192.168.10.1", "username": "admin", "passwd": "Cisco19"},
        {"ip": "192.168.20.1", "username": "admin", "passwd": "Cisco19"}
    ]
    for routers in router:
        cisco_login(routers["ip"], routers["username"], routers["passwd"])
        