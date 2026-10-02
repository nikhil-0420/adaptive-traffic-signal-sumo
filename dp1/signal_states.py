"""Derive RYG state strings for the junction straight from the built net.

Controllers never hard-code phase indices - they ask for 'axis green', 'axis yellow'
or 'all red' strings, so changing the network does not break the controller.
"""
import sumolib
from . import config as C


class SignalStates:
    def __init__(self, net_file):
        net = sumolib.net.readNet(str(net_file), withPrograms=True)
        self.links = []  # (link_index, axis, direction)
        for a in C.APPROACHES:
            edge = net.getEdge(f"{a}_in")
            for out_edge, conns in edge.getOutgoing().items():
                for c in conns:
                    self.links.append((c.getTLLinkIndex(), C.AXIS_OF[a], c.getDirection()))
        self.n = max(i for i, _, _ in self.links) + 1

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
