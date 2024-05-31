
# Client.py
# sender.py - The sender in the reliable data transfer protocol
import socket
import sys
import _thread
import time
import random
import matplotlib.pyplot as plt
import numpy as np

# Timer class from timer.py
class Timer(object):
    TIMER_STOP = -1

    def __init__(self, duration):
        self._start_time = self.TIMER_STOP
        self._duration = duration

    def start(self):
        if self._start_time == self.TIMER_STOP:
            self._start_time = time.time()

    def stop(self):
        if self._start_time != self.TIMER_STOP:
            self._start_time = self.TIMER_STOP

    def running(self):
        return self._start_time != self.TIMER_STOP

    def timeout(self):
        if not self.running():
            return False
        else:
            return time.time() - self._start_time >= self._duration

# Packet-related functions from packet.py
def make(seq_num, data = b''):
    seq_bytes = seq_num.to_bytes(4, byteorder = 'little', signed = True)
    return seq_bytes + data

def make_empty():
    return b''

def extract(packet):
    seq_num = int.from_bytes(packet[0:4], byteorder = 'little', signed = True)
    return seq_num, packet[4:]

# Unreliable data transfer functions from udt.py
DROP_PROB = 8

sent_packets = []
def send_udt(packet, sock, addr, packet_id):
    if random.randint(0, DROP_PROB) > 0:
        sock.sendto(packet, addr)
        sent_packets.append((packet_id, time.time()))  # Add packet ID and timestamp

def recv(sock):
    packet, addr = sock.recvfrom(1024)
    return packet, addr

RECEIVER_ADDR = ('localhost', 8080)
SENDER_ADDR = ('localhost', 0)
SLEEP_INTERVAL = 0.05
TIMEOUT_INTERVAL = 0.5
WINDOW_SIZE = 4
PACKET_SIZE = 512

# Shared resources across threads
base = 0
mutex = _thread.allocate_lock()
send_timer = Timer(TIMEOUT_INTERVAL)

# Sets the window size
def set_window_size(num_packets):
    global base
    return min(WINDOW_SIZE, num_packets - base)

# Send thread
def send(sock, filename):
    global mutex
    global base
    global send_timer
    retransmitted_packets = []

    # Open the file
    try:
        file = open(filename, 'rb')
    except IOError:
        print('Unable to open', filename)
        return

    # Add all the packets to the buffer
    packets = []
    seq_num = 0
    while True:
        data = file.read(PACKET_SIZE)
        if not data:
            break
        packets.append(make(seq_num, data))
        seq_num += 1

    num_packets = len(packets)
    print('I got', num_packets, 'packets')
    window_size = set_window_size(num_packets)
    next_to_send = 0
    base = 0

    # Start the receiver thread
    _thread.start_new_thread(receive, (sock,))

    while base < num_packets:
        mutex.acquire()
        # Send all the packets in the window
        while next_to_send < base + window_size:
            print('Sending packet', next_to_send)
            send_udt(packets[next_to_send], sock, RECEIVER_ADDR,next_to_send)
            next_to_send += 1

        # Start the timer
        if not send_timer.running():
            print('Starting timer')
            send_timer.start()

        # Wait until a timer goes off or we get an ACK
        while send_timer.running() and not send_timer.timeout():
            mutex.release()
            print('Sleeping')
            time.sleep(SLEEP_INTERVAL)
            mutex.acquire()

        if send_timer.timeout():
            print('Timeout, resending from', base)
            send_timer.stop()
            next_to_send = base  # Resend from base if timeout occurs
            retransmitted_packets.extend(sent_packets[base:next_to_send])  # Mark retransmitted packets
        else:
            print('Shifting window')
            window_size = set_window_size(num_packets)
        mutex.release()

    # Extract packet IDs and timestamps from sent_packets
    packet_ids, timestamps = zip(*sent_packets)

    # Create a scatter plot of packet IDs vs time
    plt.scatter(timestamps, packet_ids, color='blue', label='Sent Packets')

    # Check if any retransmitted packets exist
    if retransmitted_packets:
        # Extract retransmitted packet IDs and timestamps
        retransmitted_ids, retransmitted_timestamps = zip(*retransmitted_packets)

        # Create a scatter plot for retransmitted packets
        plt.scatter(retransmitted_timestamps, retransmitted_ids, color='red', label='Retransmitted Packets')

        # Set plot labels and title
        plt.xlabel('Time')
        plt.ylabel('Packet ID')
        plt.title('Received Packet ID vs Time')
        plt.legend()

        # Display the number of retransmissions and test parameters as part of the figure
        plt.text(0.5, 0.5, f'Retransmissions: {len(retransmitted_packets)}\nWindow Size: {WINDOW_SIZE}\nTimeout Interval: {TIMEOUT_INTERVAL}\nLoss Rate: {PACKET_LOSS_RATE}',
                 horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)

    # Show the plot
    plt.show()

    # Send empty packet as sentinel
    send_udt(make_empty(), sock, RECEIVER_ADDR)
    file.close()

# Receive thread
def receive(sock):
    global mutex
    global base
    global send_timer

    while True:
        pkt, _ = recv(sock);
        ack, _ = extract(pkt);

        # If we get an ACK for the first in-flight packet
        print('Got ACK', ack)
        if (ack >= base):
            mutex.acquire()
            base = ack + 1
            print('Base updated', base)
            send_timer.stop()
            mutex.release()

# Main function
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Expected filename as command line argument')
        exit()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SENDER_ADDR)
    filename = sys.argv[1]

    send(sock, filename)
    sock.close()