import json
import sys
import time
import zmq

def main(backend):
    # Socket to talk to server
    context = zmq.Context(io_threads=1)
    socket = context.socket(zmq.SUB)
    socket.connect(backend)
    socket.setsockopt_string(zmq.SUBSCRIBE, u"")
    # Process 5 updates
    total_recvs = 0
    while True:
        data = socket.recv_multipart()
        metadata = json.loads(data[0].decode())
        print(metadata)
        total_recvs += 1
        print("total recvs", total_recvs)

if __name__ == "__main__":
    backend = sys.argv[1]
    main(backend)
