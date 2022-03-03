import json
from pathlib import Path

import pytest
import torch
from numpy.random import RandomState

from audiotools import AudioSignal
from audiotools import util
from audiotools.data import preprocess
from audiotools.data import transforms as tfm

transforms_to_test = []
for x in dir(tfm):
    if hasattr(getattr(tfm, x), "transform"):
        if x not in ["Compose"]:
            transforms_to_test.append(x)


def _compare_transform(transform_name, data):
    regression_data = Path(f"tests/regression/transforms/{transform_name}.json")
    regression_data.parent.mkdir(exist_ok=True, parents=True)

    if regression_data.exists():
        with open(regression_data, "r") as f:
            target_data = json.load(f)
        assert data["hash"] == target_data["hash"]
    else:
        with open(regression_data, "w") as f:
            json.dump(data, f, indent=4)


@pytest.mark.parametrize("transform_name", transforms_to_test)
def test_transform(transform_name):
    seed = 0
    transform_cls = getattr(tfm, transform_name)

    kwargs = {}
    if transform_name == "BackgroundNoise":
        kwargs["csv_files"] = ["tests/audio/noises.csv"]
    if transform_name == "RoomImpulseResponse":
        kwargs["csv_files"] = ["tests/audio/irs.csv"]

    audio_path = "tests/audio/spk/f10_script4_produced.wav"
    signal = AudioSignal(audio_path, offset=10, duration=2)
    transform = transform_cls(**kwargs)

    batch = transform.instantiate(seed, signal)
    if transform_name == "FileLevelVolumeNorm":
        batch["file_loudness"] = AudioSignal(audio_path).ffmpeg_loudness().item()

    batch["signal"] = signal
    batch = transform(batch)

    output = batch["signal"]
    output_hash = output.hash()
    data = {"hash": output_hash}

    _compare_transform(transform_name, data)


def test_compose():
    seed = 0

    audio_path = "tests/audio/spk/f10_script4_produced.wav"
    signal = AudioSignal(audio_path, offset=10, duration=2)
    transform = tfm.Compose(
        [
            tfm.RoomImpulseResponse(csv_files=["tests/audio/irs.csv"]),
            tfm.BackgroundNoise(csv_files=["tests/audio/noises.csv"]),
        ]
    )

    batch = transform.instantiate(seed, signal)

    batch["signal"] = signal.clone()
    batch = transform(batch)
    output = batch["signal"]
    output_hash = output.hash()

    data = {"hash": output_hash}

    _compare_transform("Compose", data)


def test_masking():
    pass
