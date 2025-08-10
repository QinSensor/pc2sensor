UUID_MAP_BUTTON = {
    'shutdown': "1c930040-d459-11e7-9296-b8e856369374",
    'factory_reset': "1c930041-d459-11e7-9296-b8e856369374",
    'restart': "1c930042-d459-11e7-9296-b8e856369374",


    # ... Add as needed ...
}



UUID_MAP = {
    'sample_rate': "1c930023-d459-11e7-9296-b8e856369374",  # in map
    'gain': "1c930022-d459-11e7-9296-b8e856369374",         # in map
    'mode': "1c930031-d459-11e7-9296-b8e856369374",         # in map
    'holdoff_interval': "1c93003a-d459-11e7-9296-b8e856369374",  # numeric
    'wakeup_interval': "1c930036-d459-11e7-9296-b8e856369374",   # numeric
    'trace_len': "1c930024-d459-11e7-9296-b8e856369374",        # in map
    'axes': "1c93002b-d459-11e7-9296-b8e856369374",              # in map
    'trigger_delay': "1c930025-d459-11e7-9296-b8e856369374",

    # 'window': "1c930027-d459-11e7-9296-b8e856369374",
    #
    # 'trigger_level': "1c93002D-d459-11e7-9296-b8e856369374",

    # ... Add as needed ...
}

MAPPINGS = {
    # 'trigger_delay': [
    #     (10, "10"),
    #     (25, "25"),
    #     (50, "50"),
    #     (75, "75"),
    #     (90, "90")
    # ],
    'trigger_delay': [
        (0, "10"),
        (2, "25"),
        (3, "50"),
        (4, "75"),
        (5, "90")
    ],
    'axes': [
        (1, "1"),
        (3, "3")
    ],
    'sample_rate': [
        (1, "25600 Hz"),
        (2, "12800 Hz"),
        (3, "5120 Hz"),
        (4, "2560 Hz"),
        (5, "1280 Hz"),
        (6, "512 Hz"),
        (7, "256 Hz")
    ],
    'trace_len': [
        (0, "64 samples"),
        (1, "128 samples"),
        (2, "256 samples"),
        (3, "512 samples"),
        (4, "1024 samples"),
        (5, "2048 samples"),
        (6, "4096 samples"),
        (7, "8192 samples"),
        (8, "16384 samples"),
        (9, "32768 samples"),
        (10, "65536 samples"),
        (11, "131072 samples"),
        (12, "262144 samples"),
        (13, "524288 samples"),
        (14, "1048576 samples"),
        (15, "2097152 samples")
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


