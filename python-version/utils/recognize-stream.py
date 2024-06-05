#!/usr/bin/python3
#-*- encoding: Utf-8 -*-
from os.path import dirname, realpath
from argparse import ArgumentParser
from pydub import AudioSegment
from sys import stderr
from json import dumps

UTILS_DIR = realpath(dirname(__file__))

ROOT_DIR = realpath(UTILS_DIR + '/..')
FINGERPRINTING_DIR = realpath(ROOT_DIR + '/fingerprinting')

import sys
sys.path.append(FINGERPRINTING_DIR)

from communication import recognize_song_from_signature
from algorithm import SignatureGenerator

"""
    Sample usage: ./recognize-streams.py ../tests/stupeflip.wav
"""


if __name__ == '__main__':

    args = ArgumentParser(description = """
Generate a Shazam fingerprint from every minute in a sound file,
perform song recognition on each chunk using Shazam's servers and
print obtained information to the standard output.
""")
    
    args.add_argument('input_file', help = 'The .WAV or .MP3 file to recognize.')
    args.add_argument('-s', '--start', default=0, help = 'Offset in seconds to start scanning')
    args.add_argument('-l', '--signature-len', default=12, help = 'Sample length in seconds to process into signature')
    args.add_argument('-L', '--skip-len', default=60, help = 'Seconds to skip between signatures')
    
    args = args.parse_args()
    
    audio = AudioSegment.from_file(args.input_file)
    
    audio = audio.set_sample_width(2)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)
    samples = audio.get_array_of_samples()
    
    chunk_len = int(args.skip_len) # seconds
    print(f"{args.input_file} {audio.duration_seconds} seconds, {chunk_len} seconds between signatures")
    
    for chunk in range(int(args.start),int(audio.duration_seconds)-chunk_len//2, chunk_len):
        signature_generator = SignatureGenerator()
        signature_generator.feed_input(samples)
        signature_generator.MAX_TIME_SECONDS = int(args.signature_len)
        signature_generator.samples_processed += 16000 * chunk
        
        signature = signature_generator.get_next_signature()
        
        if not signature:
            print("%d: failed to get a signature", chunk)
            #print(dumps(results, indent = 4, ensure_ascii = False))
            break
        
        results = recognize_song_from_signature(signature)
        
        if not results['matches']:
            print("%d: no result yet" % (chunk))
            continue

        with open("%05d.json" % (chunk), "w") as f:
          f.write(dumps(results, indent = 4, ensure_ascii = False))

        track = results["track"]
        metadata = track["sections"][0]["metadata"]
        title = track["title"]
        artist = track["subtitle"]
        album = metadata[0]["text"] if len(metadata) > 0 else "???"
        label = metadata[1]["text"] if len(metadata) > 1 else "???"
        year = metadata[2]["text"] if len(metadata) > 2 else "???"
        print("%05d: %s / %s (%s %s)" % (chunk, title, artist, album, year))
        
