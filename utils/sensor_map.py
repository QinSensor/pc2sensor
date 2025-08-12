UUID_DATA = {
    'data': ("1c930020-d459-11e7-9296-b8e856369374", 16),  #
    'calibration': ("1c930029-d459-11e7-9296-b8e856369374", 2),  #

    'temp': ("1c930032-d459-11e7-9296-b8e856369374", 2),  #
    'time': ("1c930033-d459-11e7-9296-b8e856369374", 3),  #
    'battery': ("1c930038-d459-11e7-9296-b8e856369374", 2),  #


}



UUID_MAP_BUTTON = {
    'shutdown': "1c930040-d459-11e7-9296-b8e856369374",
    'factory_reset': "1c930041-d459-11e7-9296-b8e856369374",
    'restart': "1c930042-d459-11e7-9296-b8e856369374",

    'release': "1c930030-d459-11e7-9296-b8e856369374",


    # ... Add as needed ...
}

PARAM_LABELS = {
    "sample_rate": "Sample Rate (Hz)",
    "gain": "Gain",
    "trigger_delay": "Trigger Delay (%TBD)",
    "trace_len": "Trace Length (samples)",
    "axes": "Axes",
    "mode": "Operating Mode",
    "holdoff_interval": "Holdoff Interval (s)",
    "wakeup_interval": "Wakeup Interval (s)"
}


UUID_MAP = {
    'axes': ("1c93002b-d459-11e7-9296-b8e856369374", 1),  # in map
    'sample_rate':       ("1c930023-d459-11e7-9296-b8e856369374", 1),  # in map
    'gain':              ("1c930022-d459-11e7-9296-b8e856369374", 1),  # in map
    'mode':              ("1c930031-d459-11e7-9296-b8e856369374", 1),  # in map
    'holdoff_interval':  ("1c93003a-d459-11e7-9296-b8e856369374", 2),  # numeric
    'wakeup_interval':   ("1c930036-d459-11e7-9296-b8e856369374", 2),  # numeric, 3 bytes

    'trace_len':         ("1c930024-d459-11e7-9296-b8e856369374", 1),  # in map
    'trigger_delay':     ("1c930025-d459-11e7-9296-b8e856369374", 2),   #


    # 'window': "1c930027-d459-11e7-9296-b8e856369374",
    #
    # 'trigger_level': "1c93002D-d459-11e7-9296-b8e856369374",

    # ... Add as needed ...
}

MAPPINGS = {
    'axes': [
        (1, "1"),
        (3, "3")
    ],
    'sample_rate': [
        (1, "25600"),
        (2, "12800"),
        (3, "5120"),
        (4, "2560"),
        (5, "1280"),
        (6, "512"),
        (7, "256")
    ],
    'trace_len': [
        (0, "64"),
        (1, "128"),
        (2, "256"),
        (3, "512"),
        (4, "1024"),
        (5, "2048"),
        (6, "4096"),
        (7, "8192"),
        (8, "16384"),
        (9, "32768"),
        (10, "65536"),
        (11, "131072"),
        (12, "262144"),
        (13, "524288"),
        (14, "1048576"),
        (15, "2097152")
    ],
    'mode': [
        (1, "Continuous"),
        (2, "Wakeup"),
        (3, "Wakeup+"),
        (4, "Ready"),
        (5, "MotionDetect"),
    ],
    'gain': [
        (1, "1"),
        (2, "2"),
        (4, "4"),
        (10, "10"),
    ]
}


