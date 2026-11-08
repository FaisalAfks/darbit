"""darbit's default reader: RapidOCR's PP-OCR models on onnxruntime, from the `ocr` extra (decision 0019).

A single line goes straight to the recogniser, without looking for text first (about 9 ms against 13 ms with the
look, on 4 threads); `lines` finds each line first. The recogniser's chances are decoded here (core/reading.py), so a
read can be limited to some characters. RapidOCR is imported on the first read: it takes about a second.
"""

import threading

import numpy as np

from .reading import Reading, decode

DETECT_SIDE = 960  # the longest side the line finder looks at; RapidOCR's own default enlarges small crops (slow)


class RapidReader:
    """Reads text with RapidOCR's bundled models. Raises ImportError without the `ocr` extra."""

    def __init__(self, threads: int):
        from rapidocr import RapidOCR

        self._engine = RapidOCR(
            params={
                "Global.log_level": "warning",
                # every core by default: on a PC busy with a game, that made a read 20 times slower
                "EngineConfig.onnxruntime.intra_op_num_threads": threads,
                "EngineConfig.onnxruntime.inter_op_num_threads": 1,
                "Det.limit_type": "max",
                "Det.limit_side_len": DETECT_SIDE,
            }
        )
        # RapidOCR's own parts, below its public call, to decode with only some characters: the extra pins
        # rapidocr below 4, and tests/test_read.py checks these with the real models
        self._recogniser = self._engine._load_rec_model()
        self._alphabet = list(self._recogniser.postprocess_op.character)
        self._lock = threading.Lock()  # observers read from their own threads; one model run at a time

    def line(self, pixels: np.ndarray, allowed: str | None) -> Reading:
        """One line of text filling the pixels."""
        height, width = pixels.shape[:2]
        if height < 2 or width < 2:
            return Reading("", 0.0)
        _, model_height, model_width = self._recogniser.rec_image_shape
        shape = max(model_width / model_height, width / height)
        batch = self._recogniser.resize_norm_img(pixels, shape)[np.newaxis].astype(np.float32)
        with self._lock:
            chances = self._recogniser.session(batch)[0]
        return decode(chances, self._alphabet, allowed)

    def lines(self, pixels: np.ndarray, allowed: str | None) -> list[Reading]:
        """Each line of text in the pixels, top to bottom."""
        with self._lock:
            found = self._engine._load_det_model()(pixels)
        if found.boxes is None:
            return []
        readings = []
        for box in found.boxes:
            left, top = np.floor(box.min(axis=0)).astype(int)
            right, bottom = np.ceil(box.max(axis=0)).astype(int)
            part = pixels[max(top, 0) : bottom, max(left, 0) : right]
            reading = self.line(np.ascontiguousarray(part), allowed)
            if reading.text:
                readings.append(reading)
        return readings


def reader(threads: int) -> RapidReader:
    """The reader, for runtime/readers.py."""
    return RapidReader(threads)
