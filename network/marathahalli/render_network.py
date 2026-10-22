"""Render professional topology diagram and visualization of Marathahalli SUMO network."""

from pathlib import Path
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import sumolib

REPO_ROOT = Path(__file__).resolve().parents[2]
NET_FILE = REPO_ROOT / "network" / "marathahalli" / "dist" / "marathahalli.net.xml"
OUTPUT_PNG = REPO_ROOT / "network" / "marathahalli" / "marathahalli_network_topology.png"
ARTIFACT_PNG = Path(r"C:\Users\ACER.DESKTOP-R4G9UL6\.gemini\antigravity-ide\brain\c5864367-6c8a-4c66-bf41-473706ea3a76\marathahalli_network_topology.png")

def render_topology():
    net = sumolib.net.readNet(str(NET_FILE), withPrograms=True)

    fig, ax = plt.subplots(figsize=(15, 13), dpi=220)
    fig.patch.set_facecolor('#090d16')  # Deep dark slate
    ax.set_facecolor('#131d2e')

    # Draw grid
    ax.grid(True, linestyle=':', alpha=0.2, color='#64748b')

    # Plot all edges with distinct styling
    for edge in net.getEdges():
        eid = edge.getID()
        lanes = edge.getLanes()
        shape = edge.getShape()
        if not shape:
            continue
        xs = [pt[0] for pt in shape]
        ys = [pt[1] for pt in shape]

        if "flyover" in eid:
            # Elevated flyover bridge
            color = '#38bdf8'  # Cyan / sky blue
            lw = 5.0
            zorder = 6
        elif "mainline" in eid:
            # ORR Mainline through flow
            color = '#10b981'  # Emerald green
            lw = 4.5
            zorder = 4
        elif "slip" in eid:
            # Free-flow left turn slips
            color = '#c084fc'  # Light purple
            lw = 2.8
            zorder = 3
        elif "ramp" in eid:
            # Connector ramps to surface
            color = '#fbbf24'  # Amber
            lw = 3.2
            zorder = 3
        elif "leg" in eid:
            # Surface intersection legs
            color = '#f87171'  # Coral red
            lw = 4.5
            zorder = 5
        else:
            # Outer boundary arterials
            color = '#94a3b8'  # Slate grey
            lw = 4.0
            zorder = 2

        ax.plot(xs, ys, color=color, linewidth=lw, solid_capstyle='round', zorder=zorder)

    # Highlight the Signal-Controlled Node
    tls_node = net.getNode("marathahalli_tls")
    tx, ty = tls_node.getCoord()
    tls_circle = patches.Circle((tx, ty), radius=10, facecolor='#ef4444', edgecolor='#ffffff', linewidth=2.5, zorder=12)
    ax.add_patch(tls_circle)

    # Add signal head callout
    ax.text(tx + 22, ty - 35,
            "VERIFIED BTP SIGNAL-CONTROLLED NODE\n"
            "Node ID: marathahalli_tls\n"
            "• Program: btp_fixed (Cycle = 210s)\n"
            "• Phase 1: 105s EW Green (HAL <-> Whitefield)\n"
            "• Phase 2: 95s NS Green (ORR S <-> ORR N)\n"
            "• Clearances: 3s Yellow + 2s All-Red each phase",
            color='#ffffff', fontsize=9, fontweight='semibold',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#991b1b', edgecolor='#f87171', alpha=0.92, lw=1.5),
            zorder=15)

    # Mark Elevated Flyover
    ax.text(350, 395,
            "MARATHAHALLI FLYOVER (BRIDGE)\n"
            "Elevated Varthur Rd Overpass (Z = +7.0m)\n"
            "Continuous Dual-Lane Free-Flow (Speed: 60 km/h, No Signals)",
            color='#38bdf8', fontsize=9.5, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#082f49', edgecolor='#38bdf8', alpha=0.9, lw=1.5),
            zorder=15)

    # Mark Outer Ring Road Mainline
    ax.text(395, 230,
            "ORR MAINLINE\n"
            "Dual-Lane Underpass / Through flow\n"
            "(Grade-Separated, Zero Signal Conflict)",
            color='#10b981', fontsize=8.5, fontweight='bold', ha='left',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#064e3b', edgecolor='#10b981', alpha=0.9, lw=1.2),
            zorder=15)

    # Mark Approach Labels
    ax.text(15, 365, "WEST ENTRY: FROM HAL AIRPORT RD\n(2 Lanes Carriageway, Speed: 60 km/h)",
            color='#f8fafc', fontsize=9, fontweight='bold', ha='left',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', edgecolor='#64748b', alpha=0.85))

    ax.text(685, 365, "EAST ENTRY: TO VARTHUR / WHITEFIELD\n(2 Lanes Carriageway, Speed: 60 km/h)",
            color='#f8fafc', fontsize=9, fontweight='bold', ha='right',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', edgecolor='#64748b', alpha=0.85))

    ax.text(350, 680, "NORTH ENTRY: TO K.R. PURAM (ORR NORTH)\n(2 Lanes Carriageway, Speed: 60 km/h)",
            color='#f8fafc', fontsize=9, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', edgecolor='#64748b', alpha=0.85))

    ax.text(350, 20, "SOUTH ENTRY: TO KADUBEESANAHALLI (ORR SOUTH)\n(2 Lanes Carriageway, Speed: 60 km/h)",
            color='#f8fafc', fontsize=9, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e293b', edgecolor='#64748b', alpha=0.85))

    # Mark Free-Flow Slips
    ax.text(260, 480, "Slip Road:\nHAL -> ORR North\n(Free-Flow)", color='#c084fc', fontsize=8, ha='center', fontweight='semibold')
    ax.text(440, 480, "Slip Road:\nORR North -> Whitefield\n(Free-Flow)", color='#c084fc', fontsize=8, ha='center', fontweight='semibold')
    ax.text(440, 200, "Slip Road:\nWhitefield -> ORR South\n(Free-Flow)", color='#c084fc', fontsize=8, ha='center', fontweight='semibold')
    ax.text(260, 200, "Slip Road:\nORR South -> HAL\n(Free-Flow)", color='#c084fc', fontsize=8, ha='center', fontweight='semibold')

    # Draw E2 Detector markers on surface legs
    for edge_id in ["leg_hal_in", "leg_wf_in", "leg_orr_s_in", "leg_orr_n_in"]:
        e = net.getEdge(edge_id)
        sh = e.getShape()
        if sh:
            mid = sh[len(sh)//2]
            ax.plot(mid[0], mid[1], 's', color='#facc15', markersize=9, markeredgecolor='#000000', markeredgewidth=1.2, zorder=14)

    # Custom Legend
    legend_elements = [
        patches.Patch(color='#38bdf8', label='Marathahalli Flyover (Elevated Z=+7m, 60 km/h) [Verified]'),
        patches.Patch(color='#10b981', label='Outer Ring Road Mainline (Grade-Separated Through Flow) [Verified]'),
        patches.Patch(color='#ef4444', label='Surface Signal-Controlled Junction & Legs (marathahalli_tls) [Verified]'),
        patches.Patch(color='#fbbf24', label='Surface Connector Ramps & Slip Slopes (40 km/h) [Inferred]'),
        patches.Patch(color='#c084fc', label='Channelized Free-Flow Left Turn Slips (40 km/h) [Inferred]'),
        patches.Patch(color='#94a3b8', label='Outer Arterials (2 Lanes, 60 km/h) [Verified via OpenCity]'),
        patches.Patch(color='#facc15', label='Simulated Lane-Area (E2) Queue Detectors (25m coverage) [Model Seam]'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', facecolor='#0f172a', edgecolor='#475569', labelcolor='#f8fafc', fontsize=8.5, framealpha=0.92)

    # Compass Rose / Direction Indicator
    ax.annotate('N', xy=(0.95, 0.94), xycoords='axes fraction', fontsize=14, fontweight='bold', color='#f8fafc', ha='center',
                bbox=dict(boxstyle='circle,pad=0.3', facecolor='#1e293b', edgecolor='#38bdf8'))
    ax.annotate('↑', xy=(0.95, 0.90), xycoords='axes fraction', fontsize=16, fontweight='bold', color='#38bdf8', ha='center')

    # Scale Bar (100 metres)
    ax.plot([550, 650], [50, 50], color='#ffffff', lw=3, zorder=15)
    ax.text(600, 60, "100 metres", color='#ffffff', fontsize=8.5, ha='center', fontweight='bold', zorder=15)

    # Title & Metadata Header
    plt.title("DP1 Phase 7A: Reconstructed Marathahalli Bridge Network Topology\n"
              "Grade-Separated Varthur Rd Overpass × Outer Ring Road (ORR) × Single Verified Control Node\n"
              "Ground Truth: OpenCity (BBMP Road Centerline & Road Width KMLs) + BTP Signal Timings PDF",
              fontsize=11.5, fontweight='bold', color='#ffffff', pad=15)

    ax.set_xlim(-20, 720)
    ax.set_ylim(-10, 710)
    ax.set_xlabel("Local X Coordinate (metres)", color='#94a3b8', fontsize=9)
    ax.set_ylabel("Local Y Coordinate (metres)", color='#94a3b8', fontsize=9)
    ax.tick_params(colors='#94a3b8', labelsize=8)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=220, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Network topology diagram successfully generated at {OUTPUT_PNG}")

    if ARTIFACT_PNG.parent.exists():
        shutil.copyfile(OUTPUT_PNG, ARTIFACT_PNG)
        print(f"Copied to artifact path: {ARTIFACT_PNG}")

if __name__ == '__main__':
    render_topology()
