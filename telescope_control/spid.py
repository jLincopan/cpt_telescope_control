# Library to process all bytes formating for the SPID MD-1 Rot2Prog protocol

deg_res = 2 # 01 - 1, 02 - 0.5, 04 - 0.25, byte - degrees per pulse
stop_str = "57000000000000000000000F20"
status_str = "57000000000000000000001F20"
command_str = "5730303030PH30303030PV2F20"
restart_str = "57EFBEADDE000000000000EE20"

def angle_to_pulse(angle):
    i = str(int(deg_res * (360 + angle))) # create string of pulses
    if len(i) < 4: # Add the "0" for complet the byte string
        i = "0" + i
    return i

def build_command(az, el):
    command = list(command_str)
    az_pulse = angle_to_pulse(az)
    el_pulse = angle_to_pulse(el)

    command[3] = az_pulse[0]
    command[5] = az_pulse[1]
    command[7] = az_pulse[2]
    command[9] = az_pulse[3]

    command[10] = "0"
    command[11] = str(deg_res)

    command[13] = el_pulse[0]
    command[15] = el_pulse[1]
    command[17] = el_pulse[2]
    command[19] = el_pulse[3]

    command[20] = "0"
    command[21] = str(deg_res)
    
    return "".join(command)

def encode_command(msg):
    return bytes.fromhex(msg)

def decode_command(msg):
    response_string = msg.hex()
    H1 = int(response_string[3:4], 16)
    H2 = int(response_string[5:6], 16)
    H3 = int(response_string[7:8], 16)
    H4 = int(response_string[9:10], 16)
    V1 = int(response_string[13:14], 16)
    V2 = int(response_string[15:16], 16)
    V3 = int(response_string[17:18], 16)
    V4 = int(response_string[19:20], 16)

    # Calculate angles for Az/El
    az = round((H1 * 100) + (H2 * 10) + H3 + (H4 / 10) -360, 1)
    el = round((V1 * 100) + (V2 * 10) + V3 + (V4 / 10) -360, 1)

    return (az, el)

