import net_protocol


class send_bash:
    def __init__(self, nodes):
        self.nodes = nodes

    def send_command(self, bash):
        for node in self.nodes:
            net_protocol.send_command(self.nodes[node], bash)
