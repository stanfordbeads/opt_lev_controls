import os
import time 

start = time.time()

rsa_key = 'C:\\Users\\beads\\.ssh\\id_rsa'

ip = '171.64.58.220' #IP address of beads-router1
port = '50001' #External port of raspberrypi set on beads-router1

i = 0 
while True:
    time.sleep(0.3)
    os.system('C:\\Windows\\Sysnative\\OpenSSH\\scp.exe -i {} -P {} pi@{}:~/*txt ./'.format(rsa_key, port, ip))
    

end = time.time()


print(end-start)
