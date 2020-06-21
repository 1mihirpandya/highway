import os

class FileCache:
    def __init__(self):
        self.files = {}
        self.root = None

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
        if path in self.get(filename):
            return True
        return False

    def prune(file, path):
        if file in self.files:
            ref = self.files[filename]
            for p in range(len(ref)):
                if path == ref[p]:
                    ref = ref[:p] + ref[p + 1:]

    def remove_file(file):
        del self.files[file]

    def get_files(self):
        return list(self.files.keys())
