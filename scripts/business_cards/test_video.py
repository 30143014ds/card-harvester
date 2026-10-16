"""Integration check: independent landscape video, new geometry, native crops."""
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from business_cards.contacts import atomic_json
from business_cards.video import extract_video, prepare_video, validate_annotations


class NewVideoTest(unittest.TestCase):
    def test_new_video_does_not_depend_on_first_video_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / 'new video.avi'
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'MJPG'), 10, (640, 480))
            self.assertTrue(writer.isOpened())
            frame = np.full((480, 640, 3), 45, np.uint8)
            cv2.rectangle(frame, (55, 135), (365, 315), (245, 245, 245), -1)
            for index, text in enumerate(['ACME', 'Alice Smith', 'Director', 'alice@acme.test', '+7 916 123 45 67']):
                cv2.putText(frame, text, (72, 165 + index * 30), cv2.FONT_HERSHEY_SIMPLEX,
                            .45, (20, 20, 20), 1, cv2.LINE_AA)
            for _ in range(20):
                writer.write(frame)
            writer.release()
            job = prepare_video(video, root / 'library', interval=1)
            info = json.loads((job / 'video_info.json').read_text())
            self.assertEqual(info['source_resolution'], [640, 480])
            self.assertFalse(info['hdr'])
            annotations = {'source_sha256': info['source_sha256'], 'scenes': [
                {'id': 0, 'reference_frame': 0, 'start_sec': 0, 'end_sec': 1.8,
                 'cards': [{'id': 'card_001', 'quad': [[55, 135], [365, 135], [365, 315], [55, 315]]}]}]}
            atomic_json(job / 'annotations.json', annotations)
            result = extract_video(job, interval=.6)
            self.assertEqual(result['cards'], 1)
            manifest = json.loads((job / 'manifest.json').read_text())
            self.assertEqual(manifest['count'], 1)
            self.assertEqual(manifest['source_resolution'], [640, 480])
            crop = cv2.imread(str(job / 'cards/card_001.png'))
            self.assertLess(abs(crop.shape[1] - 310), 5)
            self.assertLess(abs(crop.shape[0] - 180), 5)
            wrong = dict(annotations, source_sha256='0' * 64)
            with self.assertRaises(ValueError):
                validate_annotations(info, wrong, [640, 480])


if __name__ == '__main__':
    unittest.main()
