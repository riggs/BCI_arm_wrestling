

from construct import (Struct, Magic, UBInt8, UBInt16, UBInt32, Optional, Embed, Enum, Array, Field,
                       BFloat32, GreedyRange, Switch, Debugger, Probe)


_header = Struct('header',
    Magic('@ABCD'),
    Enum(UBInt8('type'),
         NULL = 0,
         EEG_DATA = 1,
         EVENT = 5
    ),
    UBInt16('length'),
    UBInt32('number')
)

_null = Struct('null',
               Array(111, UBInt8('none'))
)

_event = Struct('event',
    Enum(UBInt32('code'),
         VERSION = 1,
         DATA_START = 2,
         DATA_STOP = 3,
         SENSOR_MAP = 9,
         DATA_RATE = 10
    ),
    UBInt32('sending_node'),
    Optional(UBInt32('message_length')),
    Optional(Field('message', lambda ctx: ctx.message_length or 0))
)

_EEG_data = Struct('_EEG_data',
    BFloat32('timestamp'),
    UBInt8('data_counter'),     # Unused, just 0 currently
    Field('ADC_status', 6),
    GreedyRange(BFloat32('data'))
)

DSI_streamer_packet = Struct('DSI_streamer_packet',
    Embed(_header),
    Switch('data', lambda ctx: ctx.type,
            {"NULL": Embed(_null),
             "EEG_DATA": Embed(_EEG_data),
             "EVENT": Embed(_event)}
    )
)

