import socket
import time

TCP_IP = '171.64.58.220'
TCP_PORT = 50003 

BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#s.settimeout(0.1)
s.connect((TCP_IP, TCP_PORT))

try:
    s.send('s')
    
    data = s.recv(BUFFER_SIZE)
    print('data: {}'.format(data))
     
except socket.timeout as e:
    print(e)
    pass
except socket.error as e:
    print(e)
    pass

with open('../../serial_output.txt', 'w') as output:
    output.write(data)

print('closing') 
s.close()
