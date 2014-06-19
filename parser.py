
from construct import (Struct, Magic, UBInt8, UBInt16, UBInt32, Embed, Enum, Array, Field,
                       BFloat32, Switch, If, PascalString, Debugger, Probe)


_header = Struct('embedded',
    Magic('@ABCD'),  # bytes 0-5
    Enum(UBInt8('type'),  # byte 5
         NULL=0,
         EEG_DATA=1,
         EVENT=5
    ),
    UBInt16('length'),  # bytes 6-7
    UBInt32('number'),  # bytes 8-11
)


_event = Struct('embedded',
    Enum(UBInt32('event_code'),  # bytes 12-15
         VERSION=1,
         DATA_START=2,
         DATA_STOP=3,
         SENSOR_MAP=9,
         DATA_RATE=10
    ),
    UBInt32('sending_node'),  # byes 16-19
    # Message data is optional
    If(lambda ctx: ctx.length > 8,  # Counting from 0
        # message_length: bytes 20-23, message: bytes 24+
        PascalString('message', length_field=UBInt32('message_length'), encoding='ascii')
    )
)


_EEG_data = Struct('embedded',
    BFloat32('timestamp'),  # bytes 12-15
    UBInt8('data_counter'),  # byte 16; Unused, just 0 currently
    Field('ADC_status', 6),  # bytes 17-22
    Array(lambda ctx: (ctx.length - 11)/4, BFloat32('channel_data'))  # bytes 23-26, 27-30, etc.
)


_null = Struct('embedded',
    Array(111, UBInt8('none'))
)


DSI_streamer_packet = Struct('DSI_streamer_packet',
    Embed(_header),
    Switch('payload', lambda ctx: ctx.type,
           {"NULL": Embed(_null),
            "EVENT": Embed(_event),
            "EEG_DATA": Embed(_EEG_data)}
    )
)

