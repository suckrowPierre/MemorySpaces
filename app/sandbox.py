import audioldm2
import parallel_audio_generator
import numpy as np

"""
def main():
    model_path = "../data/models/audioldm2"
    device = "cuda"
    pipe = audioldm2.setup_pipeline(model_path, device)
    parameters = audioldm2.generate_params("hello world")
    audio = audioldm2.text2audio(pipe, parameters)

    if(audio is not None):
        print("audio is not None")

"""
audio_model_settings = {
    "model": "audioldm2",
    "device": "cuda",
    "audio_length_in_s" : 10,
    "guidance_scale": 3,
    "num_inference_steps": 10,
    "negative_prompt": "low quality, average quality, noise, high pitch, artefacts",
    "num_waveforms_per_prompt": 1
}

audio_settings = {
    "device": "",
    "channel1": 1,
    "channel2": 2,
    "channel3": 3,
    "sine1_freq": 440,
    "sine2_freq": 220,
    "sine3_freq": 110,
    "sine1_volume": 0.1,
    "sine2_volume": 0.1,
    "sine3_volume": 0.1
}

llm_settings = {
    "number_soundevents": 4,
    "number_prompts": 10,
    "role_system": "Your are an intelligent system that extracts prompts from a questionnaire to be used with a generative ai model. Your primary role is to analyze and interpret the responses to this questionnaire, which is focused on eliciting detailed descriptions of personal memories that users wish to re-experience through audio. From the user's descriptions, you will identify and extract !NUMBER_SOUNDEVENTS key sound events that are pivotal to each memory. For each identified sound event, you are tasked with generating !NUMBER_PROMPTS distinct but closely related prompts. These prompts will be used by a generative AI model to create audio files that encapsulate the essence of the sound events. The challenge lies in ensuring that each set of prompts remains true to the core idea of its corresponding sound event, while introducing subtle variations to offer a range of auditory experiences. This process aims to recreate a multi-faceted and immersive auditory representation of the user's cherished memories.",
    "role_user":  "Please extract !NUMBER_SOUNDEVENTS key sound events from the following Q&A and generate !NUMBER_PROMPTS prompts for each sound event. The Q&A is focused on eliciting detailed descriptions of personal memories that users wish to re-experience through audio. The prompts will be used by a generative AI model to create audio files that encapsulate the essence of the sound events. Please ensure that each set of prompts remains true to the core idea of its corresponding sound event, while introducing subtle variations to offer a range of auditory experiences. Do not use verbs like create, generate, synthesize ... but rather just describe the audio and the scene. \n Q&A: \n"
}

def main():


    generator = parallel_audio_generator.ParallelAudioGenerator(audio_settings, audio_model_settings, llm_settings)
    cache = generator.cache
    manager = generator.manager


    model_path = "../data/models/audioldm2"
    device = "cuda"
    pipe = audioldm2.setup_pipeline(model_path, device)
    parameters = audioldm2.generate_params("hello world")
    audio = audioldm2.text2audio(pipe, parameters)

    generator.append_to_memory_space(0, "test", audio)
    generator.print_cache()
    




if __name__ == '__main__':
    main()