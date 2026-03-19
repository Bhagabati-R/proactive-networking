"""
logger.py — Console logging for the simulation stages.
"""

DIVIDER = "=" * 55


def header():
    print(f"\n{DIVIDER}")
    print("  Proactive Networking: Link-Aware Congestion Prevention")
    print(DIVIDER)


def stage(number, message):
    print(f"\n[STAGE {number}] {message}\n")


def info(message):
    print(f"  [SYSTEM] {message}")


def footer():
    print(f"\n{DIVIDER}")
    print("  Simulation complete. Close the window to exit.")
    print(f"{DIVIDER}\n")
