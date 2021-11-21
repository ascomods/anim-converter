import os
import core.utils as ut

class StringTable():
    @ut.keep_cursor_pos
    def read(self, stream, start_offset, size = None):
        """
        Inits the string table with read content from input
        """
        self.start_offset = start_offset
        stream.seek(self.start_offset)
        if size == None:
            stream.seek(0, os.SEEK_END)
            size = stream.tell() - self.start_offset
            stream.seek(self.start_offset)
        string_list = stream.read(size).split(b'\x00')
        string_list = [x for x in string_list if x != b'']
        string_list_offsets = self.gen_offsets(string_list)
        self.content = dict(zip(string_list_offsets, string_list))

    def build(self, string_list, start_offset = 0):
        self.start_offset = start_offset
        string_list_offsets = self.gen_offsets(string_list)
        self.content = dict(zip(string_list_offsets, string_list))

    def gen_offsets(self, string_list):
        """
        Generates the offsets pointing to each name in the table
        """
        string_list_offsets = [self.start_offset]
        offset = self.start_offset
        for string in string_list:
            offset += len(string) + 1
            string_list_offsets.append(offset)
        string_list_offsets.pop()
        return string_list_offsets
    
    def get_size(self):
        last_string = list(self.content.items())[-1]
        size = last_string[0] + len(last_string[1])
        if size % 16 != 0:
            size += 16 - (size % 16)
        return size
    
    def write(self, output):
        for key, val in self.content.items():
            output.write(ut.s2b_name(val) + b'\x00')
    
    def __repr__(self):
        string = (
            f'\nclass: {self.__class__.__name__}\n'
            f'size: {self.get_size()}\n'
        )
        for key, val in self.content.items():
            string += f'{key} : {val}\n'
        return string