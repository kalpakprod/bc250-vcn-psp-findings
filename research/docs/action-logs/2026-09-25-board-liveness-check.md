# Board liveness check — 2026-09-25 (session start, operator authorized live work)

Actor: laptop 127.0.0.1/24 (eno1), same L2 as board's documented DHCP lease.
Method: read-only. ICMP sweep + TCP:22 probe + ARP + hostkey compare. No writes.

## Result: BOARD OFFLINE

- Documented board IP 127.0.0.1 (doc 2026-09-25-live-vcn-harvest-ssh): ping 100% loss, NO arp entry => not on network.
- /24 sweep: 19 live hosts. Only .61/.71/.111 expose ssh:22.
  - .111 MAC 00:00:00:00:00:00 = Proxmox cluster OUI (bc:24:11), not the board.
  - .61 MAC 00:00:00:00:00:00, .71 MAC 00:00:00:00:00:00 (locally-administered/VM); both refuse our key (Permission denied) and .71 hostkey CHANGED vs known_hosts.
  - None present the board's recorded ed25519 identity (known_hosts .118 line 375).
- Conclusion: BC-250 is powered off, or its SD-card OS did not boot / did not get a DHCP lease.

## Blocker

Live reverse-engineering (DF-window unclamp S1-S5, full A1 gasket replay) needs the board reachable by ssh.
Cannot start until operator powers the board and confirms it boots to Debian + gets a lease.

## Unblock steps for operator

1. Power on BC-250, boot the Debian SD-card.
2. Confirm lease (check router, or re-run scripts/board_liveness.sh <ip>).
3. Report the IP; note board_liveness.sh uses steammachine@, harvest-doc used root@ — confirm which user is live.
