from pox.core import core
import json
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
import time
import threading
from queue import Queue
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.util import str_to_bool, dpid_to_str, str_to_dpid
import pox.openflow.libopenflow_01 as of

log = core.getLogger("iplb")

FLOW_IDLE_TIMEOUT = 10
FLOW_MEMORY_TIMEOUT = 60 * 5

class MemoryEntry(object):
    def __init__(self, server, first_packet, client_port):
        self.server = server
        self.first_packet = first_packet
        self.client_port = client_port
        self.refresh()

    def refresh(self):
        self.timeout = time.time() + FLOW_MEMORY_TIMEOUT

    @property
    def is_expired(self):
        return time.time() > self.timeout

    @property
    def key1(self):
        ethp = self.first_packet
        ipp = ethp.find('ipv4')
        tcpp = ethp.find('tcp')
        return ipp.srcip, ipp.dstip, tcpp.srcport, tcpp.dstport

    @property
    def key2(self):
        ethp = self.first_packet
        ipp = ethp.find('ipv4')
        tcpp = ethp.find('tcp')
        return self.server, ipp.srcip, tcpp.dstport, tcpp.srcport

class iplb(object):
    def __init__(self, connection, service_ip, servers=[]):
        self.service_ip = IPAddr(service_ip)
        self.servers = [IPAddr(a) for a in servers]
        self.con = connection
        self.mac = self.con.eth_addr
        self.live_servers = {}
        self.memory = {}
        self.outstanding_probes = {}
        self.probe_cycle_time = 5
        self.arp_timeout = 3
        self.knn = self._initialize_knn()

        self.server_resources = {}  # Untuk menyimpan resource server
        self.server_knn = {} #untuk menyimpan server terkecil hasil perhitungan knn
        self.data = {}
        self._do_probe()

        try:
            self.log = log.getChild(dpid_to_str(self.con.dpid))
        except:
            self.log = log
    
    def _initialize_knn(self):
        df = pd.read_csv("/home/mininet/pox/pox/misc/coba/load1.csv")
        X = df[['CPU', 'MEMORY', 'DISK']]
        y = df['STATUS SERVER']
        knn = KNeighborsClassifier(n_neighbors=3)
        knn.fit(X, y)
        return knn

    def _classify_resource(self, resource_data):
    # Mengubah setiap resource menjadi kategori LOW (0), MEDIUM (1), atau HIGH (2)
        def classify(value):
            if 0 <= value <= 30:
                return 0  # LOW
            elif 31 <= value <= 70:
                return 1  # MEDIUM
            elif 71 <= value <= 100:
                return 2  # HIGH
            else:
                return -1  # UNKNOWN, jika berada di luar rentang

        classified_data = {
        'CPU': classify(resource_data['CPU']),
        'MEMORY': classify(resource_data['MEMORY']),
        'DISK': classify(resource_data['DISK'])
        }
        return classified_data

    def _apply_knn(self, resources):
        prediction = self.knn.predict([[resources['CPU'], resources['MEMORY'], resources['DISK']]])
        return prediction[0]

    def _do_expire(self):
        t = time.time()
        for ip, expire_at in list(self.outstanding_probes.items()):
            if t > expire_at:
                self.outstanding_probes.pop(ip, None)
                if ip in self.live_servers:
                    self.log.warn("Server %s down", ip)
                    del self.live_servers[ip]

        c = len(self.memory)
        self.memory = {k: v for k, v in self.memory.items() if not v.is_expired}
        if len(self.memory) != c:
            self.log.debug("Expired %i flows", c - len(self.memory))

    def _do_probe(self):
        self._do_expire()
        server = self.servers.pop(0)
        self.servers.append(server)
        r = arp()
        r.hwtype = r.HW_TYPE_ETHERNET
        r.prototype = r.PROTO_TYPE_IP
        r.opcode = r.REQUEST
        r.hwdst = ETHER_BROADCAST
        r.protodst = server
        r.hwsrc = self.mac
        r.protosrc = self.service_ip
        e = ethernet(type=ethernet.ARP_TYPE, src=self.mac, dst=ETHER_BROADCAST)
        e.set_payload(r)
        msg = of.ofp_packet_out()
        msg.data = e.pack()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        msg.in_port = of.OFPP_NONE
        self.con.send(msg)
        self.outstanding_probes[server] = time.time() + self.arp_timeout
        core.callDelayed(self._probe_wait_time, self._do_probe)

    @property
    def _probe_wait_time(self):
        r = self.probe_cycle_time / float(len(self.servers))
        r = max(.25, r)
        return r

    def _pick_server(self, key, inport):
    # Memilih server dengan resource terkecil dari server_knn
        lowest_server = min(self.server_knn.items(), key=lambda x: x[1])

    # Cek apakah IPAddr server terkecil ada di live_servers
        for server_ip, status in self.server_knn.items():
            if server_ip in self.live_servers and status == lowest_server[1]:
                self.log.debug("Server dengan IPAddr yang sesuai di live_servers: %s", server_ip)
                return server_ip  # Kembalikan IPAddr dari server di live_servers yang cocok

    # Jika tidak ada server yang cocok di live_servers, kembalikan lowest_server default
        self.log.debug("Memilih server dengan resource terkecil secara default: %s", lowest_server[0])
        return lowest_server[0]


    def _handle_PacketIn(self, event):
        inport = event.port
        packet = event.parsed

        def drop():
            if event.ofp.buffer_id is not None:
                msg = of.ofp_packet_out(data=event.ofp)
                self.con.send(msg)
            return None

        tcpp = packet.find('tcp')
        udpp = packet.find('udp')
        if udpp:
            ipp = packet.find('ipv4')
            server_ip = ipp.srcip
            resource_data = json.loads(udpp.payload)  # Misal payload UDP berisi data JSON resource

            # Klasifikasikan resource server
            classified_resources = self._classify_resource(resource_data)
        
            # Simpan resource dan hasil K-NN untuk server
            if server_ip not in self.server_resources or self.server_resources[server_ip] != classified_resources:
                self.server_resources[server_ip] = classified_resources

                # Hitung K-NN untuk mendapatkan status server
                status = self._apply_knn(classified_resources)
                self.server_knn[server_ip] = status
            
                self.log.debug("Update K-NN Server %s, Status: %s", self.server_knn)
                self.log.debug("Updated resources from server %s: %s", server_ip, classified_resources)
            return
        if tcpp and (tcpp.dstport == 80 or tcpp.srcport == 80):
            ipp = packet.find('ipv4')

            if ipp.srcip in self.servers:
                key = ipp.srcip, ipp.dstip, tcpp.srcport, tcpp.dstport
                entry = self.memory.get(key)

                if entry is None:
                    self.log.debug("No client for %s", key)
                    return drop()

                entry.refresh()
                mac, port = self.live_servers[entry.server]

                actions = []
                actions.append(of.ofp_action_dl_addr.set_src(self.mac))
                actions.append(of.ofp_action_nw_addr.set_src(self.service_ip))
                actions.append(of.ofp_action_output(port=entry.client_port))
                match = of.ofp_match.from_packet(packet, inport)

                msg = of.ofp_flow_mod(command=of.OFPFC_ADD, idle_timeout=FLOW_IDLE_TIMEOUT,
                                  hard_timeout=of.OFP_FLOW_PERMANENT, data=event.ofp,
                                  actions=actions, match=match)
                self.con.send(msg)
            elif ipp.dstip == self.service_ip:
                key = ipp.srcip, ipp.dstip, tcpp.srcport, tcpp.dstport
                entry = self.memory.get(key)

                if entry is None or entry.server not in self.live_servers:
                    if len(self.live_servers) == 0:
                        self.log.warn("No servers!")
                        return drop()
                # Traffic baru, ambil server berdasarkan resource yang telah disimpan
                server = self._pick_server(key, inport)
                self.log.debug("Directing traffic to %s", server)
                entry = MemoryEntry(server, packet, inport)
                self.memory[entry.key1] = entry
                self.memory[entry.key2] = entry

                entry.refresh()
                mac, port = self.live_servers[entry.server]

                actions = []
                actions.append(of.ofp_action_dl_addr.set_dst(mac))
                actions.append(of.ofp_action_nw_addr.set_dst(entry.server))
                actions.append(of.ofp_action_output(port=port))
                match = of.ofp_match.from_packet(packet, inport)

                msg = of.ofp_flow_mod(command=of.OFPFC_ADD, idle_timeout=FLOW_IDLE_TIMEOUT,
                                  hard_timeout=of.OFP_FLOW_PERMANENT, data=event.ofp,
                                  actions=actions, match=match)
                self.con.send(msg)
        if not tcpp:
            arpp = packet.find('arp')
            if arpp:
                if arpp.opcode == arpp.REPLY:
                    if arpp.protosrc in self.outstanding_probes:
                        del self.outstanding_probes[arpp.protosrc]
                        if (self.live_servers.get(arpp.protosrc, (None, None)) == (arpp.hwsrc, inport)):
                            pass
                        else:
                            self.live_servers[arpp.protosrc] = arpp.hwsrc, inport
                            self.log.info("Server %s up", arpp.protosrc)
                return drop()

            return drop()


_dpid = None

def launch (ip, servers, dpid = None):
  global _dpid
  if dpid is not None:
    _dpid = str_to_dpid(dpid)

  servers = servers.replace(","," ").split()
  servers = [IPAddr(x) for x in servers]
  ip = IPAddr(ip)


  # We only want to enable ARP Responder *only* on the load balancer switch,
  # so we do some disgusting hackery and then boot it up.
  from proto.arp_responder import ARPResponder
  old_pi = ARPResponder._handle_PacketIn
  def new_pi (self, event):
    if event.dpid == _dpid:
      # Yes, the packet-in is on the right switch
      return old_pi(self, event)
  ARPResponder._handle_PacketIn = new_pi

  # Hackery done.  Now start it.
  from proto.arp_responder import launch as arp_launch
  arp_launch(eat_packets=False,**{str(ip):True})
  import logging
  logging.getLogger("proto.arp_responder").setLevel(logging.WARN)


  def _handle_ConnectionUp (event):
    global _dpid
    if _dpid is None:
      _dpid = event.dpid

    if _dpid != event.dpid:
      log.warn("Ignoring switch %s", event.connection)
    else:
      if not core.hasComponent('iplb'):
        # Need to initialize first...
        core.registerNew(iplb, event.connection, IPAddr(ip), servers)
        log.info("IP Load Balancer Ready.")
      log.info("Load Balancing on %s", event.connection)

      # Gross hack
      core.iplb.con = event.connection
      event.connection.addListeners(core.iplb)


  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)