"""Run a TMCM-1231 in "Profile Position Mode" using PDOs to configure Six-Point Ramp

Includes the recording and plotting of the actual velocity along with the actual position.

"""
import time
import dataclasses
import canopen
import matplotlib.pyplot as plt
from pytrinamic.modules.canopen_node import TmcmNode


samples = []


@dataclasses.dataclass
class Sample:
    timestamp: float
    position: int
    velocity: int


def tpdo4_callback(message):
    global samples
    position = message['Position Actual Value 1'].raw
    velocity = message['Velocity Actual Value 1'].raw
    timestamp = message.timestamp
    samples.append(Sample(timestamp=timestamp, position=position, velocity=velocity))


with canopen.Network() as network:
    network.connect(channel='PCAN_USBBUS1', bustype='pcan', bitrate=1_000_000)

    tmcm_1231 = TmcmNode(1, 'TMCM-1231.eds')
    network.add_node(tmcm_1231)

    # Reconfiguration of TPDO4
    tmcm_1231.sdo[0x1803][1].raw = 0x8000_0381  # disable the TPDO4
    tmcm_1231.sdo[0x1a03][0].raw = 0            # write the number of entries into subindex 0
    tmcm_1231.sdo[0x1a03][1].raw = 0x60640020
    tmcm_1231.sdo[0x1a03][2].raw = 0x606C0020
    tmcm_1231.sdo[0x1a03][0].raw = 2            # write the number of entries into subindex 0
    tmcm_1231.sdo[0x1803][1].raw = 0x4000_0381  # enable the TPDO4

    # Reconfiguration of RPDO4
    tmcm_1231.sdo[0x1403][1].raw = 0x8000_0381  # disable the RPDO4
    tmcm_1231.sdo[0x1603][0].raw = 0            # write the number of entries into subindex 0
    tmcm_1231.sdo[0x1603][1].raw = 0x60400010
    tmcm_1231.sdo[0x1603][2].raw = 0x607a0020
    tmcm_1231.sdo[0x1603][0].raw = 2            # write the number of entries into subindex 0
    tmcm_1231.sdo[0x1403][1].raw = 0x4000_0381  # enable the RPDO4

    tmcm_1231.load_configuration()
    tmcm_1231.nmt.state = 'OPERATIONAL'

    tmcm_1231.go_to_operation_enabled()
    tmcm_1231.tpdo[4].add_callback(tpdo4_callback)

    tmcm_1231.sdo['Absolute Max Current 1'].raw = 50
    tmcm_1231.sdo['Stop On Stall 1'].raw = 0

    # Setting axis parameters for configuring SixPoint ramp
    tmcm_1231.sdo['Profile start velocity 1'].raw = 5000            # V_Start
    tmcm_1231.sdo['Profile start acceleration 1'].raw = 5000        # A1
    tmcm_1231.sdo['Profile Acceleration 1'].raw = 30000             # max acceleration
    tmcm_1231.sdo['Profile Deceleration 1'].raw = 20000             # max deceleration
    tmcm_1231.sdo['Profile break velocity 1'].raw = 10000           # V1
    tmcm_1231.sdo['Profile final deceleration 1'].raw = 5000        # D1
    tmcm_1231.sdo['Profile Velocity in pp-mode 1'].raw = 40000      # V_max

    # Need to set V_stop and ramp_wait_time with an appropriate value
    tmcm_1231.sdo['End velocity 1'].raw = 5000                      # V_Stop?
    # tmcm_1231.sdo['Profile stop deceleration 1'].raw = 5000
    tmcm_1231.sdo['Bow scaling factor 1'].raw = 255                 # ramp_wait_time?

    # Profile Velocity Mode
    tmcm_1231.sdo['Modes of Operation 1'].raw = tmcm_1231.ModeOfOperation.PROFILE_POSITION_MODE

    tmcm_1231.rpdo[4]['Controlword 1'].raw = tmcm_1231.Cmd.ENABLE_OPERATION
    tmcm_1231.rpdo[4]['Target Position 1'].raw = 0
    tmcm_1231.rpdo[4].transmit()

    time.sleep(0.2)

    for target_position in [100000, 0]:
        tmcm_1231.rpdo[4]['Target Position 1'].raw = target_position
        tmcm_1231.rpdo[4]['Controlword 1'].raw = tmcm_1231.Cmd.ENABLE_OPERATION + tmcm_1231.Cmd.NEW_SET_POINT
        tmcm_1231.rpdo[4].transmit()

        tmcm_1231.rpdo[4]['Controlword 1'].raw = tmcm_1231.Cmd.ENABLE_OPERATION
        tmcm_1231.rpdo[4].transmit()

        target_reached_flag_mask = 0x0400
        while tmcm_1231.sdo['Statusword 1'].raw & target_reached_flag_mask == 0:
            pass

        print("Reached Target Position: {target_position}" .format(target_position=target_position))

    tmcm_1231.nmt.state = 'PRE-OPERATIONAL'
    tmcm_1231.shutdown()

fig, ax = plt.subplots(2)
t = [float(s.timestamp - samples[0].timestamp) for s in samples]
pos = [float(s.position) for s in samples]
vel = [float(s.velocity) for s in samples]
ax[0].plot(t, pos, label='Position')
ax[0].set_title('Pos vs Time')
ax[0].set_xlabel('Time')
ax[0].set_ylabel('Pos')
ax[0].legend()
ax[0].grid()
ax[1].plot(t, vel, label='Velocity')
ax[1].set_title('Vel vs Time')
ax[1].set_xlabel('Time')
ax[1].set_ylabel('Vel')
ax[1].legend()
ax[1].grid()
plt.show()