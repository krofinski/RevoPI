import sys
from bluepy.btle import Scanner, DefaultDelegate, Peripheral
from time import sleep

my_device="REVO_DUAL_AXIS_TABLE"
commands=["+CR,TILTVALUE=","+CT,TURNANGLE=", "+CT,TURNSPEED=", "+CT,TOZERO;", "+CR,TILTVALUE=0;", "+QT,CHANGEANGLE;"]
commands_supported=8
NULL_CHAR = chr(0)

def write_report(report):
    with open('/dev/hidg0', 'rb+') as fd:
        fd.write(report.encode())

def send_space():
  write_report(NULL_CHAR*2+chr(44)+NULL_CHAR*5)
  write_report(NULL_CHAR*8)

def send_command(c, command):
    c.write(bytes(command, "utf-8"))

def extract_angle(input):
  input_filtered=input[8:]
  angle=float(input_filtered[:-2])
  return angle
	

def command_check(entries):
  if entries[0]=="#":
    return "comment"
  else:
    commands=entries.split(',')
    if (len(commands)-1) == commands_supported:
      return commands
    else:
      return "error"

def wait_for_end(c, command):
  response_1="first_measurement"
  response_2="second_measurement"
  while response_1 != response_2:
    send_command(c, command)
    response_1=c.read()
    send_command(c, command)
    response_2=c.read()
  
def read_args(c,args):
#  print(args)
  tilt_angle=args[0]
  rotation_angle=args[1]
  steps=int(args[2])
  delay_step=int(args[3])
  delay=int(args[4])
  speed=args[5]
  reset_tilt=args[6]
  reset_rotation=args[7]
  mode_scan=args[8]
  tilt=commands[0]+tilt_angle+';'
  rotation=commands[1]+rotation_angle+';'
  rotation_speed=commands[2]+speed+';'
  if reset_rotation == "Partial":
    send_command(c,  commands[5])
    output=c.read()
    initial_angle=extract_angle(str(output))

  send_command(c, tilt)
  sleep(delay)
  send_command(c, rotation_speed) 

  for step in range(steps):
    send_space()
    sleep(delay_step-1)
    send_command(c, rotation)
    wait_for_end(c, commands[5])
    if 'C' in mode_scan:
      send_space()
    sleep(1)
  if reset_rotation == "Partial":
    send_command(c,  commands[5])
    output=c.read()
    final_angle=extract_angle(str(output))
    rotation_angle=str(round(-1*(final_angle-initial_angle),1))
    rotation=commands[1]+rotation_angle+';' 
    send_command(c, rotation)
    wait_for_end(c, commands[5])
  elif reset_rotation== "Total":
    speed="36"
    rotation_speed=commands[2]+speed+';'
    send_command(c, rotation_speed)
    send_command(c, commands[3])
    wait_for_end(c, commands[5])
    sleep(delay)
  if reset_tilt == "True":
    send_command(c, commands[4])
    sleep(delay)

def read_file(c):
  file=open(my_file, "r")
  commands_list=file.readlines()
  for entries in commands_list:
    commands=command_check(entries)
    if commands=="error":
      print("File contains errors!")
    elif commands != "comment":
      read_args(c,commands)
    else:
      pass
#      print("comment in file")
  
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        pass

if len(sys.argv)==2:
  my_file=sys.argv[1]
else:
  print("Input file missing or number of parameters incorrect!")
  sys.exit()

scanner = Scanner().withDelegate(ScanDelegate())
try:
  devices = scanner.scan(10.0)
except:
  devices = scanner.scan(10.0)

for dev in devices:
  device=dev.getValueText(9)
  if type(device) == str:
    if my_device in device:
      turntable_addr=dev.addr
#      print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
      for (adtype, desc, value) in dev.getScanData():
#        print("%d,  %s = %s" % (adtype, desc, value))
        if adtype == 3:
          my_char=value

p=Peripheral()
try:
  p.connect(turntable_addr, addrType='random')
except:
#except BTLEException:
  print ("Already connected")

c=p.getCharacteristics(uuid=my_char)[0]

read_file(c)

#send_command(c)

'''
lc=p.getCharacteristics(uuid=my_char)
for c in lc:
  print("UUID %s, properties %s, Handler %d" %(c.uuid, c.propertiesToString(), c.getHandle()))
  send_command(c)


ls = p.getServices()
for s in ls:
  print(s.uuid)
  lc = s.getCharacteristics()
  for c in lc:
    print("UUID %s, properties %s, Handler %d" %(c.uuid, c.propertiesToString(), c.getHandle()))
    send_command(c)
    sleep(5)
'''

p.disconnect()


