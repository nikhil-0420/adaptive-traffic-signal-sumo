"""Derive RYG state strings for the junction straight from the built net.

Controllers never hard-code phase indices - they ask for 'axis green', 'axis yellow'
or 'all red' strings, so changing the network does not break the controller.
"""
import sumolib
from . import config as C

MARATHAHALLI_APPROACH_EDGES = {
    "N": "leg_orr_n_in",
    "S": "leg_orr_s_in",
    "E": "leg_wf_in",
    "W": "leg_hal_in",
}


class SignalStates:
    def __init__(self, net_file, tls_id=None):
        net = sumolib.net.readNet(str(net_file), withPrograms=True)
        self.links = []  # (link_index, axis, direction)

        # Detect edge naming convention
        if net.hasEdge("N_in"):
            edge_map = {a: f"{a}_in" for a in C.APPROACHES}
        elif net.hasEdge(MARATHAHALLI_APPROACH_EDGES["N"]):
            edge_map = MARATHAHALLI_APPROACH_EDGES
        else:
            edge_map = {a: f"{a}_in" for a in C.APPROACHES if net.hasEdge(f"{a}_in")}

        for a, edge_id in edge_map.items():
            if net.hasEdge(edge_id):
                edge = net.getEdge(edge_id)
                for out_edge, conns in edge.getOutgoing().items():
                    for c in conns:
                        self.links.append((c.getTLLinkIndex(), C.AXIS_OF[a], c.getDirection()))
        self.n = max((i for i, _, _ in self.links), default=-1) + 1

    def green(self, axis):
        s = ["r"] * self.n
        for i, ax, d in self.links:
            if ax == axis:
                s[i] = "g" if d == "l" else "G"   # left turns yield (permissive)
        return "".join(s)

    def yellow(self, axis):
        s = ["r"] * self.n
        for i, ax, _ in self.links:
            if ax == axis:
                s[i] = "y"
        return "".join(s)

    def all_red(self):
        return "r" * self.n

