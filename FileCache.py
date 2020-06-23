import os

class CachedFileInfo:
    def __init__(self, addr):
        self.addr = addr
        self.persistance = 1

class FileCache:
    def __init__(self):
        self.files = {}
        self.cached_files = {}
        self.root = None

    def store(self, filename, addr):
        addr = tuple(addr)
        if filename in self.cached_files:
            self.cached_files[filename].addr = addr
            self.cached_files[filename].persistance += 1
        else:
            self.cached_files[filename] = CachedFileInfo(addr)
        #for filename in self.cached_files:
        #    print(filename, self.cached_files[filename].addr)

    def add(self, file, path=None):
        if not path:
            path = os.path.join(self.root, file)
        if file in self.files:
            self.files[file].append(path)
        else:
            self.files[file] = [path]

    def get(self, filename):
        if filename in self.files:
            return self.files[filename]
        return None

    def check(self, filename, path):
        paths = self.get(filename)
        if paths and path in paths:
            return True
        return False

    def prune(self, file, path):
        if file in self.files:
            self.files[file].remove(path)

    def remove_file(self, file):
        del self.files[file]

    def get_files(self):
        return list(self.files.keys())
