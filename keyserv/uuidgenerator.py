from baseconv import BaseConverter, BASE16_ALPHABET
from uuid import UUID, uuid4

BASE = 16
HEX_DOUBLE_WORD_LENGTH = 8
HEX_DOUBLE_WORD_UPPER_BYTE = slice(-HEX_DOUBLE_WORD_LENGTH, -(HEX_DOUBLE_WORD_LENGTH - 2))
MAX_DOUBLE_WORD = (1 << 31)
OLD_BIT_FLAG = 0x80
NEW_BIT_FLAG_MASK = OLD_BIT_FLAG - 1
BASE16 = BaseConverter(BASE16_ALPHABET.lower())

class UUIDGenerator():
    uuid = None

    def __init__(self):
        while True:
            uuid = uuid4()
            replacer = BASE16.encode(int(BASE16.decode(str(uuid)[HEX_DOUBLE_WORD_UPPER_BYTE])) & NEW_BIT_FLAG_MASK)
            if int(replacer, BASE) >= 16:
                break
        self.uuid = UUID(str(uuid)[:-(HEX_DOUBLE_WORD_LENGTH)] + replacer + str(uuid)[-(HEX_DOUBLE_WORD_LENGTH-2):])

    @staticmethod
    def new_version(uuid):
        return not bool(int(BASE16.decode(str(uuid)[HEX_DOUBLE_WORD_UPPER_BYTE])) & OLD_BIT_FLAG)

    @staticmethod
    def int_to_uuid(int_id):
        int_id = int(int_id)
        myid = str(uuid4())

        replacer1 = BASE16.encode(MAX_DOUBLE_WORD - int_id)
        replacer2 = BASE16.encode(int(BASE16.decode(myid[HEX_DOUBLE_WORD_UPPER_BYTE])) | OLD_BIT_FLAG)
        return UUID(replacer1 + myid[HEX_DOUBLE_WORD_LENGTH:-(HEX_DOUBLE_WORD_LENGTH)] +
                    replacer2 + myid[-(HEX_DOUBLE_WORD_LENGTH-2):])

    @staticmethod
    def uuid_to_int(uuid):
        inverse_id = int(BASE16.decode(uuid[:HEX_DOUBLE_WORD_LENGTH]))
        return (MAX_DOUBLE_WORD - inverse_id)

    @staticmethod
    def str_to_uuid(str_uuid):
        try:
            return UUID(hex=str_uuid)
        except:
            raise ValueError("UUID (%s provided is NOT a proper uuid" % str_uuid)


    @staticmethod
    def format_uuid_hex(uuid_str):
        if len(uuid_str) != 32:
            raise ValueError("UUID (%s provided is NOT a proper uuid" % uuid_str)

        return uuid_str[:7]+'-'+uuid_str[7:11]+'-'+uuid_str[11:15]+'-'+uuid_str[15:19]+'-'+uuid_str[19:]

