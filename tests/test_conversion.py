import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'frames_to_mp4.py'
sys.path.insert(0, str(SCRIPT.parent))
from frames_to_mp4 import natural_key


class ConversionTests(unittest.TestCase):
    def test_natural_order(self):
        names = [Path(name) for name in ['frame10.png', 'frame2.png', 'frame1.png']]
        self.assertEqual([p.name for p in sorted(names, key=natural_key)],
                         ['frame1.png', 'frame2.png', 'frame10.png'])

    def test_encode_and_preserve_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "frames with spaces and 'quotes'"
            source.mkdir()
            for number, color in [(1, (255, 0, 0)), (2, (0, 255, 0)), (10, (0, 0, 255))]:
                (source / f'frame{number}.ppm').write_bytes(b'P6\n17 19\n255\n' + bytes(color) * (17 * 19))
            output = root / 'nested' / 'test.mp4'
            command = [sys.executable, str(SCRIPT), '-s', str(source), '-d', str(output), '--fps', '12']
            subprocess.run(command, check=True, capture_output=True)
            probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams',
                                    '-of', 'json', str(output)], check=True, capture_output=True, text=True)
            stream = json.loads(probe.stdout)['streams'][0]
            self.assertEqual(stream['codec_name'], 'h264')
            self.assertEqual(stream['pix_fmt'], 'yuv420p')
            self.assertEqual((stream['width'], stream['height']), (18, 20))
            self.assertEqual(int(stream['nb_read_frames']), 3)
            self.assertEqual(stream['r_frame_rate'], '12/1')
            self.assertAlmostEqual(float(stream['duration']), 0.25, places=3)
            pixels = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-f', 'rawvideo',
                                     '-pix_fmt', 'rgb24', '-'], check=True, capture_output=True).stdout
            for index, expected in enumerate([0, 1, 2]):
                pixel = pixels[index * 18 * 20 * 3:index * 18 * 20 * 3 + 3]
                self.assertEqual(max(range(3), key=lambda c: pixel[c]), expected)
            original = output.read_bytes()
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(output.read_bytes(), original)
            subprocess.run(command + ['--overwrite'], check=True, capture_output=True)
            (source / 'frame2.ppm').write_bytes(b'broken image')
            original = output.read_bytes()
            self.assertNotEqual(subprocess.run(command + ['--overwrite'], capture_output=True).returncode, 0)
            self.assertEqual(output.read_bytes(), original)
