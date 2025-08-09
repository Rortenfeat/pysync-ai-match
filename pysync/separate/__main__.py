from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter
import argparse
import os
import random
import json

def is_media(filename):
    media_ext = ['.mp3', '.wav', '.flac', '.ape', '.alac', '.aac', '.ogg', '.oga', '.m4a', '.m4v', '.mp4', '.wma', '.wmv', '.webm', '.mkv', '.avi', '.mov', '.mpg', '.mpeg', '.3gp', '.flv']
    return os.path.splitext(filename)[1].lower() in media_ext

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", type=str, help="Audio file(directory) containing complete track")
    parser.add_argument("output", type=str, help="Directory to store separated audio files")
    parser.add_argument("--task-id", default=None, type=str, help="If specified, will write a json file with information")

    args = parser.parse_args().__dict__

    input_files = []
    if os.path.isdir(args['input']):
        for file in os.listdir(args['input']):
            if is_media(file):
                input_files.append(os.path.join(args['input'], file))
    elif os.path.isfile(args['input']):
        input_files.append(args['input'])
    else:
        print(f"Input file(s) {args['input']} not found")
        exit(1)

    output_dir = args['output']
    if not os.path.exists(output_dir): os.mkdir(output_dir)
    
    print(f'Output files will be in {output_dir}')

    # Separate vocal from music
    sep = Sep(output_dir)

    sep.separate_multi(input_files)

    if args['task_id']:
        file = os.path.join(output_dir, f'task_{args["task_id"]}.json')
        print(f"Writing task information to {file}")
        sep.save_hash(file)

class Sep:
    def __init__(self, output_dir):
        # 初始化 Spleeter 分离器
        self.separator = Separator('spleeter:2stems')
        # 获取默认的音频加载器，它会自动使用 ffmpeg (如果可用)
        self.audio_loader = AudioAdapter.default()
        self.output_dir = output_dir
        self.hash_map = {} # 避免与内置的 hash 函数重名，改名为 hash_map
        self.sample_rate = 44100 # Spleeter 默认的采样率
        print("Separator initialized")

    def separate_single(self, filename):
        print(f"Processing: {filename}")
        try:
            # 1. 加载音频文件为波形数据
            waveform, _ = self.audio_loader.load(filename, sample_rate=self.sample_rate)
            
            # 2. 执行分离，这会返回一个字典 {'vocals': numpy.ndarray, 'accompaniment': numpy.ndarray}
            prediction = self.separator.separate(waveform)
            
            # 3. 为本次分离生成一个唯一的标识符
            random_hash = random.randbytes(4).hex()
            base_filename = os.path.splitext(os.path.basename(filename))[0]

            # 4. 分别保存人声和伴奏
            vocal_path = os.path.join(self.output_dir, f'{base_filename}_vocals_{random_hash}.wav')
            accompaniment_path = os.path.join(self.output_dir, f'{base_filename}_accompaniment_{random_hash}.wav')
            
            # 使用音频适配器保存文件
            self.audio_loader.save(vocal_path, prediction['vocals'], self.sample_rate, codec='wav')
            self.audio_loader.save(accompaniment_path, prediction['accompaniment'], self.sample_rate, codec='wav')

            print(f"  -> Vocal saved to {vocal_path}")
            print(f"  -> Accompaniment saved to {accompaniment_path}")

            # 5. 记录文件路径
            self.hash_map[filename] = {
                'vocal': vocal_path,
                'accompaniment': accompaniment_path
            }
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            # 这里可以记录错误，或者直接跳过
    
    def separate_multi(self, input_files):
        # 逐个分离文件
        for file in input_files:
            self.separate_single(file)
        
    def save_hash(self, file):
        # 保存文件哈希表到 JSON
        with open(file, 'w') as f:
            json.dump(self.hash_map, f, indent=4) # indent=4 格式化输出，更易读
if __name__ == '__main__':
    cli()