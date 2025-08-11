import whisperx
import torch
import math
import argparse
import os
import json
import gc
from langdetect import detect

os.environ['HF_HOME'] = 'whisperx_models' 

def detect_language(text):
    result = detect(text)
    if result in ['zh-cn', 'zh-tw']:
        result = 'zh'
    return result

def format_time(t):
    minute: str = '{:02d}'.format(math.floor(t // 60))
    second: str = '{:02d}'.format(math.floor(t % 60))
    centisecond: str = '{:02d}'.format(int(math.floor(t * 100) % 100))
    return f"[{minute}:{second}.{centisecond}]"


def print_lrcs(task, output_dir):
    for input_file in task.keys():
        print(f'----------{input_file}----------')
        words = task[input_file]['alignment']['word_segments']
        result = ''
        for word in words:
            print(f'{format_time(word["start"])}{word["word"]}')
            result += f'{format_time(word["start"])}{word["word"]}\n'
        output_file = os.path.join(output_dir, f'{os.path.basename(input_file).split(".")[0]}.lrc')
        with open(output_file, 'w') as f:
            f.write(result)
        print(f'----------{input_file} end----------', flush=True)

def get_original_lyrics(task):
    for input_file in task.keys():
        input_dir = os.path.dirname(input_file)
        input_name = os.path.basename(input_file).split('.')[0]
        lyrics_file = os.path.join(input_dir, f'{input_name}.txt')
        lines = []
        with open(lyrics_file, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                trimmed = line.strip()
                if trimmed:
                    lines.append(trimmed)
        task[input_file]['original_lyrics'] = lines

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", type=str, help="Directory containing separated audios and task information")
    parser.add_argument("output", type=str, help="Directory to store synced lyrics(.lrc)")
    parser.add_argument("taskid", type=str, help="The JSON file containing task information")

    args = parser.parse_args().__dict__

    input_dir = args['input']
    task_file = os.path.join(input_dir, f'task_{args["taskid"]}.json')
    task: dict[str, dict[str, str]] = json.load(open(task_file, 'r'))

    # input_files = task.keys()

    output_dir = args['output']
    if not os.path.exists(output_dir): os.mkdir(output_dir)
    
    print(f'Output files will be in {output_dir}')

    get_original_lyrics(task)
    print('Original lyrics have been loaded.')

    speech = Speech(task)
    speech.recognize_all()

    with open(task_file, 'w') as f:
        json.dump(task, f, indent=4)

    for input_file in task.keys():
        print(f'Generating lyrics for {input_file}')
        lyric = Lyric(task[input_file], os.path.basename(input_file).split('.')[0], output_dir)
        lyric.save_lrc()
        lyric.save_karaoke()
    
    with open(task_file, 'w') as f:
        json.dump(task, f, indent=4)
    print('All synchronization works have been completed.')

class Speech: 
    def __init__(self, task, model_size = 'medium', device = 'cuda', batch_size = 2, compute_type = 'int8'):
        self.task: dict = task
        self.model_size = model_size
        self.device = device
        self.batch_size = batch_size
        self.compute_type = compute_type
    
    def recognize_all(self):
        language_set = set()
        for input_file in self.task.keys():
            language = detect_language(' '.join(self.task[input_file]['original_lyrics']))
            self.task[input_file]['language'] = language
            language_set.add(language)
            print(f'Language of {input_file} is detected as {language}')

        for language in language_set:
            print(f'Loading align model for {language} language...')
            model_a, metadata= whisperx.load_align_model(language_code=language, device=self.device)
            print(f'Align model loaded: {language} on {self.device}')

            for input_file in self.task.keys():
                if self.task[input_file]['language'] == language:
                    vocal_file = self.task[input_file]['vocal']
                    vocal = whisperx.load_audio(vocal_file)
                    vocal_duration = vocal.shape[0] / 16000
                    segments=  [{'start': 0.0, 'end': vocal_duration, 'text': ' '.join(self.task[input_file]['original_lyrics'])}]
                    result = whisperx.align(segments, model_a, metadata, vocal, device=self.device, return_char_alignments=False)
                    self.task[input_file]['alignment'] = result
            del model_a
            gc.collect()
            torch.cuda.empty_cache()

        print('All vocal files have been aligned.')
            

    # deprecated
    def recognize_all_(self):
        print('Loading Whisper model...')
        model = whisperx.load_model(self.model_size, self.device, compute_type=self.compute_type, download_root='whisperx_models')
        print(f'Whisper model loaded: {self.model_size} on {self.device} with {self.compute_type} precision')
        print('Start transcribing all vocal files...')
        language_set = set()
        for input_file in self.task.keys():
            vocal_file = self.task[input_file]['vocal']
            vocal = whisperx.load_audio(vocal_file)
            result = model.transcribe(vocal, self.batch_size, print_progress=True)
            # self.task[input_file]['transcription'] = result
            language_set.add(result['language'])

        print('All vocal files have been transcribed.')
        del model
        gc.collect()
        torch.cuda.empty_cache()

        for language in language_set:
            print(f'Loading align model for {language} language...')
            model_a, metadata= whisperx.load_align_model(language_code=language, device=self.device)
            print(f'Align model loaded: {language} on {self.device}')
            print(f'Start aligning all vocal files in {language}...')
            for input_file in self.task.keys():
                if self.task[input_file]['transcription']['language'] == language:
                    vocal_file = self.task[input_file]['vocal']
                    vocal = whisperx.load_audio(vocal_file)
                    result = whisperx.align(self.task[input_file]['transcription']['segments'], model_a, metadata, vocal, device=self.device, return_char_alignments=False)
                    self.task[input_file]['alignment'] = result

        print('All vocal files have been aligned.')
        del model_a
        gc.collect()
        torch.cuda.empty_cache()

class Lyric:
    def __init__(self, data, title, output_dir):
        self.data = data
        self.title = title
        self.output_dir = output_dir
        self.len_list = [len(line) for line in self.data['original_lyrics']]
        self.plain_lyrics = ''.join(self.data['original_lyrics'])
        self.formatted_lyrics = ''
        self.formatted_karaoke = ''
        self.align = []
        self.align_lyrics()
    
    def format_time(self,t) -> str:
        minute: str = '{:02d}'.format(math.floor(t // 60))
        second: str = '{:02d}'.format(math.floor(t % 60))
        centisecond: str = '{:02d}'.format(int(math.floor(t * 100) % 100))
        return f"{minute}:{second}.{centisecond}"

    def parse_index(self, index) -> tuple[int, int]:
        line_index = 0
        while index >= self.len_list[line_index] and line_index < len(self.len_list) - 1:
            index -= self.len_list[line_index]
            line_index += 1
        return line_index, index

    def align_lyrics(self) -> None:
        self.align = []
        last = 0
        for word_segment in self.data['alignment']['word_segments']:
            word = word_segment['word']
            found = False
            for p in range(last, len(self.plain_lyrics)-len(word)+1):
                for q in range(len(word)):
                    if self.plain_lyrics[p+q] != word[q]:
                        break
                else:
                    found = True
                    last = p+q
                    self.align.append({
                        'i': self.parse_index(p),
                        't': word_segment['start'],
                    })
                if found: break

    def format_lyrics(self) -> None:
        if not self.align: return

        line_time = [0] * len(self.len_list)
        for a in self.align:
            line_index = a['i'][0]
            if line_time[line_index] == 0:
                line_time[line_index] = a['t']
        formatted_lyrics = ''
        for i in range(len(self.len_list)):
            formatted_lyrics += f"[{self.format_time(line_time[i])}]{self.data['original_lyrics'][i]}\n"
        self.formatted_lyrics = formatted_lyrics.strip()

    def format_karaoke(self) -> None:
        if not self.align: return

        line_time = [0] * len(self.len_list)
        word_time = [[ [0, -1] ] for _ in range(len(self.len_list))]
        for a in self.align:
            line_index, char_index = a['i']
            if line_time[line_index] == 0:
                line_time[line_index] = a['t']
            word_time[line_index].append([char_index, a['t']])
        sliced_lyrics = [[] for _ in range(len(self.len_list))]
        formatted_karaoke = ''
        for i in range(len(word_time)): # i is line index
            formatted_karaoke += f'[{self.format_time(line_time[i])}]'
            word_time[i].append([self.len_list[i], -1])
            for j in range(len(word_time[i])-1): # j is word index
                sliced_lyrics[i].append(self.data['original_lyrics'][i][word_time[i][j][0]:word_time[i][j+1][0]])
            formatted_karaoke += sliced_lyrics[i].pop(0)
            word_time[i].pop(0)
            while len(sliced_lyrics[i]) > 0:
                formatted_karaoke += f'<{self.format_time(word_time[i].pop(0)[1])}>{sliced_lyrics[i].pop(0)}'
            formatted_karaoke += '\n'
        self.formatted_karaoke = formatted_karaoke.strip()

    def save_lrc(self) -> None:
        if not self.formatted_lyrics: self.format_lyrics()

        output_file = os.path.join(self.output_dir, f'{self.title}.lrc')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.formatted_lyrics)
        print(f'Lyrics saved to {output_file}')

    def save_karaoke(self) -> None:
        if not self.formatted_karaoke: self.format_karaoke()

        output_file = os.path.join(self.output_dir, f'{self.title}_karaoke.lrc')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.formatted_karaoke)
        print(f'Karaoke lyrics saved to {output_file}')

if __name__ == '__main__':
    cli()

import numpy as np
np.float64(15.742)