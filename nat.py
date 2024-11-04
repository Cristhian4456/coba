from mininet.cli import CLI

from mininet.log import lg, info

from mininet.topolib import TreeNet

from mininet.node import RemoteController, OVSKernelSwitch



if __name__ == '__main__':

    lg.setLogLevel('info')

    net = TreeNet(depth=1, fanout=4, waitConnected=True)



    # Add a remote controller

    c1 = RemoteController('c1', ip='127.0.0.1', port=6633)

    net.addController(c1)



    # Use OVSKernelSwitch as the default switch type

    net.addSwitch('s1', cls=OVSKernelSwitch)



    # Add NAT connectivity

    net.addNAT().configDefault()

    net.start()



    info("*** Hosts are running and should have internet connectivity\n")

    info("*** Type 'exit' or control-D to shut down network\n")

    CLI(net)



    # Shut down NAT

    net.stop()