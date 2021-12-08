import struct
import core.utils as ut

class ANM:
    dataOffset = ut.b2i(b'\x94')
    commandOffset = ut.b2i(b'\x90')

    boneList = [
        "BONE_NULL", "BONE_PRG_RESERVE", "BONE_RESERVE", "BONE_WAIST", "BONE_TAIL1", "BONE_TAIL2", "BONE_TAIL3", "BONE_TAIL4", 
        "BONE_HIP_R", "BONE_THIGH_R", "BONE_SHANK_R", "BONE_HEEL_R",
        "BONE_HIP_L", "BONE_THIGH_L", "BONE_SHANK_L", "BONE_HEEL_L",
        "BONE_BELLY", "BONE_BREAST", 
        "BONE_CLAVICLE_R", "BONE_SHOULDER_R", "BONE_ELBOW_R", 
        "BONE_WRIST_R", "BONE_THUMB_R", "BONE_FOREFINGER1_R", "BONE_FOREFINGER2_R", "BONE_MIDDLE_FINGER1_R", "BONE_MIDDLE_FINGER2_R", "BONE_MEDICINAL_FINGER1_R", 
        "BONE_MEDICINAL_FINGER2_R", "BONE_LITTLE_FINGER1_R", "BONE_LITTLE_FINGER2_R", "BONE_EFFECT_R", 
        "BONE_CLAVICLE_L", "BONE_SHOULDER_L", "BONE_ELBOW_L", 
        "BONE_WRIST_L", "BONE_THUMB_L", "BONE_FOREFINGER1_L", "BONE_FOREFINGER2_L", "BONE_MIDDLE_FINGER1_L", "BONE_MIDDLE_FINGER2_L", "BONE_MEDICINAL_FINGER1_L", 
        "BONE_MEDICINAL_FINGER2_L", "BONE_LITTLE_FINGER1_L", "BONE_LITTLE_FINGER2_L", "BONE_EFFECT_L",
        "BONE_NECK", "BONE_HEAD", "BONE_FACE", "BONE_CHIN", 
        "BONE_HAIR", "BONE_ALPHA", "BONE_THROW", "BONE_CAMERA", "BONE_UTILITY"
    ]
    
    def __init__(self, name):
        self.name = name
    
    @ut.keep_cursor_pos
    def readCommandBytes(self, stream):
        stream.seek(self.commandOffset)
        self.commandsBytes = stream.read(self.commandsCount * 16)

    @ut.keep_cursor_pos
    def readBytesAt(self, stream, offset, length):
        stream.seek(offset)
        return stream.read(length)

    @ut.keep_cursor_pos
    def readBoneData(self, stream, offset, boneName):
        stream.seek(offset)
        dataType = struct.unpack("<h", stream.read(2))[0]
        dataType = 'rotation' if dataType == 1 else 'translation'
        frameCount = struct.unpack("<h", stream.read(2))[0]
        dataStartOffset = stream.tell()
        dataSize = 8 if dataType == 'rotation' else 24
        dataBlockLength = frameCount * dataSize

        for i in range(frameCount):
            if dataType == 'rotation':
                rotationFloat = self.readRotation(stream, boneName)
                frameBytes = self.readBytesAt(stream, dataStartOffset + dataBlockLength + i * 2, 2)
                frame = struct.unpack("<h", frameBytes)[0]

                if frame not in self.data[boneName] :
                    self.data[boneName][frame] = {}
                self.data[boneName][frame][dataType] = rotationFloat
            elif dataType == 'translation':
                translationFloat = struct.unpack("<fff", stream.read(12))
                frame = struct.unpack("<i", stream.read(4))[0]

                if frame not in self.data[boneName] :
                    self.data[boneName][frame] = {}
                self.data[boneName][frame][dataType] = \
                    (translationFloat[2], translationFloat[1], translationFloat[0])
                self.data[boneName][frame]['rotation'] = self.readRotation(stream, boneName)

    def readRotation(self, stream, boneName = None):
        # Getting 3 bytes for each axis
        rotationBytes = stream.read(8)
        rotationFloat = struct.unpack("<q", rotationBytes)[0]
        rotationBytes = struct.pack(">q", rotationFloat)

        rotation1Float = self.getDegRotation((rotationFloat & 0x0fffffffffffffff) >> 40)
        rotation2Float = self.getDegRotation((rotationFloat & 0x000000ffffffffff) >> 20)
        rotation3Float = self.getDegRotation(rotationFloat & 0x00000000000fffff)

        if (rotationBytes[0] >> 4) == ut.b2i(b'\x00'):
            rotationXFloat = rotation1Float
            rotationYFloat = rotation2Float
            rotationZFloat = rotation3Float
        elif (rotationBytes[0] >> 4) == ut.b2i(b'\x01'):
            rotationXFloat = rotation2Float
            rotationYFloat = rotation1Float
            rotationZFloat = rotation3Float
        elif (rotationBytes[0] >> 4) == ut.b2i(b'\x02'):
            rotationXFloat = rotation2Float
            rotationYFloat = rotation3Float
            rotationZFloat = rotation1Float
        else:
            rotationXFloat = rotation3Float
            rotationYFloat = rotation2Float
            rotationZFloat = rotation1Float

        return (rotationXFloat, rotationYFloat, rotationZFloat)

    def read(self, stream):
        # Reading ANM Header
        self.unknown0x00 = ut.b2i(stream.read(1))
        self.commandsCount = ut.b2i(stream.read(1))
        if self.commandsCount > 0:
            self.readCommandBytes(stream)
        self.frameCount = struct.unpack("<h", stream.read(2))[0]
        self.unknown0x04 = ut.b2i(stream.read(2))
        self.data = {}

        for boneName in self.boneList:
            self.data[boneName] = {}
            offset = struct.unpack("<h", stream.read(2))[0] * 4
            if offset > 0:
                self.readBoneData(stream, offset, boneName)

    def load(self, data, frameCount = 0):
        self.data = data
        self.unknown0x00 = ut.b2i(b'\x61')
        self.commandsCount = 0
        self.frameCount = frameCount
        self.unknown0x04 = 0

        # Reorganizing data
        self.data = {}
        for boneName in self.boneList:
            if boneName not in data:
                data[boneName] = {}
            if boneName not in self.data:
                self.data[boneName] = {}
            
            lastTranslation = (0,0,0,1)
            lastRotation = (0,0,0)

            for frame in data[boneName]:
                # Removing all translations except for RESERVE BONE
                if boneName not in ["BONE_RESERVE", "BONE_THROW", "BONE_CAMERA", "BONE_UTILITY"] \
                    and 'translation' in data[boneName][frame]:
                    del data[boneName][frame]['translation']
                if 'translation' in data[boneName][frame]:
                    if 'translation' not in self.data[boneName]:
                        self.data[boneName]['translation'] = {}
                    lastTranslation = data[boneName][frame]['translation']
                    self.data[boneName]['translation'][frame] = lastTranslation
                if 'rotation' in data[boneName][frame]:
                    if 'rotation' not in self.data[boneName]:
                        self.data[boneName]['rotation'] = {}
                    lastRotation = data[boneName][frame]['rotation']
                    self.data[boneName]['rotation'][frame] = lastRotation
            
            if len(self.data[boneName]) == 1:
                if lastTranslation != (0,0,0,1):
                    self.data[boneName]['translation'][self.frameCount] = lastTranslation
                if lastRotation != (0,0,0):
                    self.data[boneName]['rotation'][self.frameCount] = lastRotation

    def getDataSize(self, boneName):
        dataSize = 4 # include dataType and frameCount
        translationSize = 0
        rotationSize = 0

        for dataType in self.data[boneName]:
            if dataType == 'translation':
                for frame in self.data[boneName][dataType]:
                    translationSize += 24
            elif dataType == 'rotation' and 'translation' not in self.data[boneName]:
                for frame in self.data[boneName][dataType]:
                    rotationSize += 10

        dataSize += translationSize + rotationSize

        return dataSize

    def write(self, stream):
        # Writing ANM Header
        stream.write(struct.pack("<b", self.unknown0x00))
        stream.write(struct.pack("<b", self.commandsCount))
        stream.write(struct.pack("<h", self.frameCount))
        stream.write(struct.pack("<h", self.unknown0x04))
        
        # Writing bone entries
        dataOffset = self.dataOffset
        for boneName in self.boneList:

            if self.data[boneName] == {}:
                stream.write(bytes(2))
            else:
                stream.write(struct.pack("<h", int(dataOffset / 0x4)))
                dataOffset += self.getDataSize(boneName)
                dataOffset = ut.add_padding(dataOffset, 4)

        stream.seek(self.dataOffset)
        for boneName in self.boneList:
            if self.data[boneName] != {}:
                for dataType in self.data[boneName]:
                    frameCount = len(self.data[boneName][dataType])

                    if dataType == 'translation':
                        stream.write(struct.pack("<h", 0))
                        stream.write(struct.pack("<h", frameCount))
                        for frame in self.data[boneName][dataType]:
                            translationData = self.data[boneName][dataType][frame]
                            translationData = struct.pack("<fffi", *translationData[:3], frame)
                            stream.write(translationData)
                            if ('rotation' in self.data[boneName]) and (frame in self.data[boneName]['rotation']):
                                stream.write(self.getRotationBytes(self.data[boneName]['rotation'][frame]))
                            else:
                                stream.write(struct.pack("<q", 0x37FFFF7FFFF7FFFF))
                    elif dataType == 'rotation' and 'translation' not in self.data[boneName]:
                        stream.write(struct.pack("<h", 1))
                        stream.write(struct.pack("<h", frameCount))
                        for frame in self.data[boneName][dataType]:
                            stream.write(self.getRotationBytes(self.data[boneName][dataType][frame]))
                        for frame in self.data[boneName][dataType]:
                            stream.write(struct.pack("<h", frame))
                    
                    paddedPosition = ut.add_padding(stream.tell(), 4)
                    stream.seek(paddedPosition)

    def getDegRotation(self, data):
        return (float(data / 0xfffff) * 180) - 90
    
    def getRotation(self, data):
        return float((data + 90) / 180) * 0xfffff
    
    def getRotationBytes(self, data):
        rotationX = round(self.getRotation(data[0]))
        rotationY = round(self.getRotation(data[1])) << 20
        rotationZ = round(self.getRotation(data[2])) << 40

        return struct.pack("<q", 0x3000000000000000 | (rotationX | rotationY | rotationZ))