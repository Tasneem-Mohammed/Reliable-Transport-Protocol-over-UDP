# receiver.py - The receiver in the reliable data transfer protocol
import socket
import sys
import random
import time

# packet.py - Packet-related functions

# Creates a packet from a sequence number and byte data
def make(seq_num, data = b''):
    seq_bytes = seq_num.to_bytes(4, byteorder = 'little', signed = True)
    return seq_bytes + data

# Creates an empty packet
def make_empty():
    return b''

# Extracts sequence number and data from a non-empty packet
def extract(packet):
    seq_num = int.from_bytes(packet[0:4], byteorder = 'little', signed = True)
    return seq_num, packet[4:]

# udt.py - Unreliable data transfer using UDP

DROP_PROB = 8

# Send a packet across the unreliable channel
# Packet may be lost
def send(packet, sock, addr):
    if random.randint(0, DROP_PROB) > 0:
        sock.sendto(packet, addr)
    return

# Receive a packet from the unreliable channel
def recv(sock):
    packet, addr = sock.recvfrom(1024)
    return packet, addr

RECEIVER_ADDR = ('localhost', 8080)

# Receive packets from the sender
def receive(sock, filename):
    # Open the file for writing
    try:
        file = open(filename, 'wb')
    except IOError:
        print('Unable to open', filename)
        return

    expected_num = 0
    received_packets = {}  # Dictionary to store out-of-order packets

    while True:
        # Get the next packet from the sender
        pkt, addr = recv(sock)
        if not pkt:
            break
        seq_num, data = extract(pkt)
        print('Got packet', seq_num)

        # If it's the expected packet, write to file and send ACK
        if seq_num == expected_num:
            print('Got expected packet')
            print('Sending ACK', expected_num)
            pkt = make(expected_num)
            send(pkt, sock, addr)
            expected_num += 1
            file.write(data)

            # Check for any subsequent packets stored in the buffer
            while expected_num in received_packets:
                print('Writing buffered packet', expected_num)
                file.write(received_packets[expected_num])
                del received_packets[expected_num]
                expected_num += 1

        elif seq_num > expected_num:
            # Store out-of-order packets in the buffer
            print('Out of order packet', seq_num, 'buffering')
            received_packets[seq_num] = data
            # Send ACK for the last in-order packet
            pkt = make(expected_num - 1)
            send(pkt, sock, addr)

        else:
            # Duplicate packet, send ACK again
            print('Duplicate packet', seq_num, 'sending ACK', expected_num - 1)
            pkt = make(expected_num - 1)
            send(pkt, sock, addr)

    # Close the file when done
    file.close()

# Main function
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Expected filename as command line argument')
        exit()
        
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(RECEIVER_ADDR) 
    filename = sys.argv[1]
    receive(sock, filename)
    sock.close()