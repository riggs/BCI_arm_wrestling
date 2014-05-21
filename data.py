

from construct import (Struct, Magic, UBInt8, UBInt16, UBInt32, Optional, Embed, Enum, String, Array, Field, OneOf)


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
    Optional(Field('message', lambda ctx: ctx.message_length))
)

_null = Struct('null',
    Array(111, UBInt8('none'))
)

DSI_streamer_packet = Struct('DSI_streamer_packet',
    Embed(_header),
    OneOf() # FIXME
)

