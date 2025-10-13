#!/bin/bash
# Network optimization for Discord bot stability

# TCP keepalive settings
echo 'net.ipv4.tcp_keepalive_time = 600' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_keepalive_intvl = 60' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_keepalive_probes = 3' >> /etc/sysctl.conf

# Apply settings
sysctl -p

echo "Network optimizations applied. Reboot recommended."