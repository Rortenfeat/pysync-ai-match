from spleeter.separator import Separator
from tempfile import TemporaryDirectory
import os

class Sep:
    def __init__(self):
        self.separator = Separator('spleeter:2stems')
        if not os.path.exists('temp'): os.mkdir('temp')
        self.temp_dir = TemporaryDirectory(prefix='separate-', dir='temp')
        print("Separator initialized")

    def separate_single(self, filename):
        # Use spleeter to separate into files in a temporary directory, and return a reference to the directory
        self.separator.separate_to_file(filename, self.temp_dir.name, filename_format='{filename}_{instrument}.{codec}')
        return os.path.join(self.temp_dir.name, f'{os.path.splitext(os.path.basename(filename))[0]}_vocals.wav')
    
    def __del__(self):
        self.temp_dir.cleanup()