import whisperx
import torch
import math
import argparse
import os
import json
import gc

os.environ['HF_HOME'] = 'whisperx_models' 

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

    speech = Speech(task)
    speech.recognize_all()

    with open(task_file, 'w') as f:
        json.dump(task, f, indent=4)
    print('Done.')

class Speech: 
    def __init__(self, task, model_size = 'medium', device = 'cuda', batch_size = 2, compute_type = 'int8'):
        self.task: dict = task
        self.model_size = model_size
        self.device = device
        self.batch_size = batch_size
        self.compute_type = compute_type
    
    def recognize_all(self):
        print('Loading Whisper model...')
        model = whisperx.load_model(self.model_size, self.device, compute_type=self.compute_type, download_root='whisperx_models')
        print(f'Whisper model loaded: {self.model_size} on {self.device} with {self.compute_type} precision')
        print('Start transcribing all vocal files...')
        language_set = set()
        for input_file in self.task.keys():
            vocal_file = self.task[input_file]['vocal']
            vocal = whisperx.load_audio(vocal_file)
            result = model.transcribe(vocal, self.batch_size, print_progress=True)
            self.task[input_file]['transcription'] = result
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

    
if __name__ == '__main__':
    cli()