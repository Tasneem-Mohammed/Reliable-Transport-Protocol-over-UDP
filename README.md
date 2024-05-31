## Computer Networks Project

### Implementation of Reliable Transport Protocol Using Go-Back-N (GBN) Protocol over UDP

#### Date: 14/5/2024



### 1. Introduction
This project aimed to implement a reliable transport protocol utilizing the Go-Back-N (GBN) protocol over UDP. The GBN protocol enhances the reliability of UDP by enabling the sender to transmit multiple packets without awaiting acknowledgments while maintaining a limited number of unacknowledged packets in the pipeline.

### 2. Implementation Details
#### - GBN Algorithm:
   - GBN ensures cumulative acknowledgments, enabling the sender to slide its window forward upon receiving acknowledgments.
#### - Sender Implementation:
   - The sender script takes 3 arguments: filename, receiver IP address, and receiver port.
   - It divides the file into smaller chunks, assigns unique packet and file IDs, and appends a trailer indicating the end of the file.
   - The sender transmits packets in a sliding window manner, waiting for acknowledgments and handling timeout events.
#### - Receiver Implementation:
   - Upon receiving packets, the receiver parses the headers and trailers to identify the file and packet IDs.
   - If the received packet is the expected one, it stores the application data; otherwise, it discards the data.
   - The receiver sends acknowledgments for correctly received packets, advancing the expected packet ID.


### Client.py
```python
# Client.py
# sender.py - The sender in the reliable data transfer protocol
  

### Server.py
```python
# Server.py
# receiver.py - The receiver in the reliable data transfer protocol
