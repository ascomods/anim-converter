import struct
import core.utils as ut
from core.StringTable import StringTable
import os

class SPA:
    boneEntrySize = 48
    translationDataSize = 16
    rotationDataSize = 8

    def __init__(self, name):
        self.name = name
        self.stringTable = StringTable()
    
    def read(self, stream):
        # Reading SPA Header
        self.offset = stream.tell()
        self.unknown0x00 = ut.b2i(stream.read(4))
        self.nameOffset = ut.b2i(stream.read(4))

        # Reading the entire string table
        self.stringTable.read(stream, self.nameOffset)
        self.unknown0x08 = ut.b2i(stream.read(4))
        self.keyframeCount = struct.unpack(">f", stream.read(4))[0]
        self.boneCount = ut.b2i(stream.read(4))
        self.entriesOffset = ut.b2i(stream.read(4))
        self.data = {}

        for i in range(self.boneCount):
            stream.seek(self.entriesOffset + self.boneEntrySize * i)

            # Reading bone entry
            boneNameOffset = ut.b2i(stream.read(4))
            boneName = ut.b2s_name(self.stringTable.content[boneNameOffset])
            unknown0x04 = ut.b2i(stream.read(4))
            translationBlockCount = ut.b2i(stream.read(4))
            rotationBlockCount = ut.b2i(stream.read(4))
            unknown0x10 = ut.b2i(stream.read(4))
            translationFrameOffset = ut.b2i(stream.read(4))
            rotationFrameOffset = ut.b2i(stream.read(4))
            unknown0x1C = ut.b2i(stream.read(4))
            translationFloatOffset = ut.b2i(stream.read(4))
            rotationFloatOffset = ut.b2i(stream.read(4))
            self.data[boneName] = {}

            # Reading bone translation data
            for j in range (translationBlockCount):
                stream.seek(translationFrameOffset + 4 * j)
                translationFrame = int(struct.unpack(">f", stream.read(4))[0])
                stream.seek(translationFloatOffset + 16 * j)
                translationFloat = struct.unpack(">ffff", stream.read(16))
                if translationFrame not in self.data[boneName] :
                    self.data[boneName][translationFrame] = {}
                self.data[boneName][translationFrame]['translation'] = \
                    translationFloat
            
            # Reading bone rotation data
            for j in range (rotationBlockCount):
                stream.seek(rotationFrameOffset + 4 * j)
                rotationFrame = int(struct.unpack(">f", stream.read(4))[0])
                stream.seek(rotationFloatOffset + 8 * j)

                # Getting 3 bytes for each axis
                rotationBytes = stream.read(8)
                rotationFloat = struct.unpack(">q", rotationBytes)[0]

                rotation1Float = self.getDegRotation((rotationFloat & 0x0fffffffffffffff) >> 40)
                rotation2Float = self.getDegRotation((rotationFloat & 0x000000ffffffffff) >> 20)
                rotation3Float = self.getDegRotation(rotationFloat & 0x00000000000fffff)

                if (rotationBytes[0] >> 4) == ut.b2i(b'\x01'):
                    rotationXFloat = -rotation2Float
                    rotationYFloat = rotation1Float
                    rotationZFloat = -rotation3Float
                else:
                    rotationXFloat = rotation1Float
                    rotationYFloat = rotation2Float
                    rotationZFloat = rotation3Float
                
                if rotationFrame not in self.data[boneName] :
                    self.data[boneName][rotationFrame] = {}
                self.data[boneName][rotationFrame]['rotation'] = \
                    (rotationXFloat, rotationYFloat, rotationZFloat, rotationBytes[0])

    def load(self, data, keyframeCount = 0):
        # Getting used bones names only
        self.data = {k: v for k, v in data.items() if v != {}}
        self.stringList = list(self.data.keys())
        
        # Adding file name
        name = os.path.splitext(os.path.basename(self.name))[0]
        self.stringList.insert(0, f"anim_{name}.mb")

        self.unknown0x00 = 0
        self.nameOffset = 0
        self.unknown0x08 = 5
        self.keyframeCount = keyframeCount
        self.boneCount = len(self.data)
        self.entriesOffset = ut.b2i(b'\x30')
        self.dataOffset = self.entriesOffset + (self.boneCount * self.boneEntrySize)
        self.nameOffset = self.entriesOffset + self.getDataSize()
        self.stringTable.build(self.stringList, self.nameOffset)

    def getDataSize(self):
        dataSize = 0
        
        for boneName in self.data:
            dataSize += self.boneEntrySize
            translationSize = 0
            rotationSize = 0

            # Frames
            for frameNum in self.data[boneName]:
                if 'translation' in self.data[boneName][frameNum]:
                    translationSize += 4
                if 'rotation' in self.data[boneName][frameNum]:
                    rotationSize += 4
            dataSize += ut.add_padding(translationSize) + ut.add_padding(rotationSize)

            translationSize = 0
            rotationSize = 0

            # Data
            for frameNum in self.data[boneName]:
                if 'translation' in self.data[boneName][frameNum]:
                    translationSize += self.translationDataSize
                if 'rotation' in self.data[boneName][frameNum]:
                    rotationSize += self.rotationDataSize
            dataSize += ut.add_padding(translationSize) + ut.add_padding(rotationSize)
        return dataSize

    def write(self, stream):
        # Writing string table
        stream.seek(self.nameOffset)
        self.stringTable.write(stream)

        # Writing SPA Header
        stream.seek(0)
        stream.write(ut.i2b(self.unknown0x00))
        stream.write(ut.i2b(self.nameOffset))
        stream.write(ut.i2b(self.unknown0x08))
        stream.write(struct.pack(">f", self.keyframeCount))
        stream.write(ut.i2b(self.boneCount))
        stream.write(ut.i2b(self.entriesOffset))
        stream.write(bytes(4) + ut.i2b(self.dataOffset))
        stream.write(bytes(4) + ut.i2b(self.dataOffset))
        stream.write(bytes(8))

        # Writing bones entries
        nextBlockOffset = self.dataOffset
        
        for boneName in self.data:
            nameOffset = ut.search_index_dict(self.stringTable.content, boneName)
            stream.write(ut.i2b(nameOffset))
            stream.write(ut.i2b(2)) # unknown0x04
            
            translationBlockCount = 0
            rotationBlockCount = 0
            for frameNum in self.data[boneName]:
                if 'translation' in self.data[boneName][frameNum]:
                    translationBlockCount += 1
                if 'rotation' in self.data[boneName][frameNum]:
                    rotationBlockCount += 1

            stream.write(ut.i2b(translationBlockCount))
            stream.write(ut.i2b(rotationBlockCount))

            stream.write(bytes(4)) # unknown0x10
            translationFrameOffset = nextBlockOffset
            stream.write(ut.i2b(translationFrameOffset))

            rotationFrameOffset = translationFrameOffset + ut.add_padding(4 * translationBlockCount)
            stream.write(ut.i2b(rotationFrameOffset))
            translationFloatOffset = rotationFrameOffset + ut.add_padding(4 * rotationBlockCount)
            stream.write(ut.i2b(translationFloatOffset)) # unknown0x1C
            stream.write(ut.i2b(translationFloatOffset))
            rotationFloatOffset = translationFloatOffset + \
                ut.add_padding(self.translationDataSize * translationBlockCount)
            stream.write(ut.i2b(rotationFloatOffset))
            nextBlockOffset = rotationFloatOffset + \
                ut.add_padding(self.rotationDataSize * rotationBlockCount)
            stream.write(ut.i2b(nextBlockOffset))
            stream.write(bytes(4)) # unknown0x2C

            nextEntryOffset = stream.tell()

            i = 0
            j = 0
            # Write data
            for frameNum in self.data[boneName]:
                if 'translation' in self.data[boneName][frameNum]:
                    stream.seek(translationFrameOffset + 4 * i)
                    stream.write(struct.pack(">f", frameNum))
                    stream.seek(translationFloatOffset + 16 * i)
                    stream.write(struct.pack(">ffff", *self.data[boneName][frameNum]['translation']))
                    i += 1
                
                if 'rotation' in self.data[boneName][frameNum]:
                    stream.seek(rotationFrameOffset + 4 * j)
                    stream.write(struct.pack(">f", frameNum))
                    stream.seek(rotationFloatOffset + 8 * j)

                    rotationX = round(self.getRotation(self.data[boneName][frameNum]['rotation'][0]))
                    rotationY = round(self.getRotation(self.data[boneName][frameNum]['rotation'][1])) << 20
                    rotationZ = round(self.getRotation(self.data[boneName][frameNum]['rotation'][2])) << 40

                    rotationBytes = struct.pack(">q", 0x3000000000000000 | (rotationX | rotationY | rotationZ))

                    stream.write(rotationBytes)
                    j += 1
            
            stream.seek(nextEntryOffset)

    def getDegRotation(self, data):
        return (float(data / 0x7ffff) * 90) - 90
    
    def getRotation(self, data):
        return (float(data + 90) / 90) * 0x7ffff