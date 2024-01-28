from enum import Enum
import numpy
import transformers
import torch
from diffusers import AudioLDM2Pipeline

print("Loaded audioldm2 module")

class Devices(Enum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"


SAMPLE_RATE = 16000


def setup_pipeline(model_path, device):
    if model_path is None:
        raise ValueError("model_path must be specified")
    if device is None:
        raise ValueError("device must be specified")
    
    if "audioldm2" not in model_path:
        raise ValueError("only audioldm2 models are supported")

    dtype = torch.float32 if device != Devices.CUDA.value else torch.float16
    pipe = AudioLDM2Pipeline.from_pretrained(model_path, torch_dtype=dtype).to(device)
    if device == "mps":
        pipe.enable_attention_slicing()
    return pipe


def validate_params(params: dict):
    required_params = [
        "prompt",
        "audio_length_in_s",
        "guidance_scale",
        "num_inference_steps",
        "negative_prompt",
        "num_waveforms_per_prompt",
    ]
    for param in required_params:
        if params.get(param) is None:
            raise ValueError(f"{param} must be specified")

    for key in params:
        if key not in required_params:
            raise ValueError(f"Parameter {key} is not a valid parameter")


def generate_params(prompt):
    return {
        "prompt": prompt,
        "audio_length_in_s": 10,
        "guidance_scale": 3,
        "num_inference_steps": 10,
        "negative_prompt": "low quality, average quality, noise, high pitch, artefacts",
        "num_waveforms_per_prompt": 1,
    }


def text2audio(pipe, parameters):
    validate_params(parameters)
    print(f"Generating audio for prompt: {parameters.get('prompt')}")
    waveforms = pipe(**parameters)["audios"]
    return waveforms[0]