import argparse
import os

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("music", type=str, help="Audio file containing complete track")
    parser.add_argument("lyrics", type=str, help="File containing song lyrics to be synced")
    parser.add_argument("--output_file", type=str, default=None, help="Output file name, defaults to name_of_mp3.lrc")

    args = parser.parse_args().__dict__

    music_file = args['music']
    lyrics_file = args['lyrics']

    if args['output_file']:
        output_file = args['output_file']
    else:
        output_file = os.path.splitext(os.path.basename(music_file))[0] + '.lrc'
    print(f'Output file will be {output_file}')

    # Separate vocal from music
    from separate import Sep
    sep = Sep()

    vocal_file = sep.separate_single(music_file)
    print(f'Vocal file is {vocal_file}')

    from sync import Sync
    sync: Sync = Sync()

    segments = sync.get_segments(vocal_file)

    # file = open(args['lyrics'], 'r')
    # full_lyrics = file.read()
    # file.close()

    del sep

    # file = open(output_file, 'w')
    # file.writelines(sync.sync_segments(full_lyrics, segments))
    # file.close()

cli()