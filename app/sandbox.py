import parallel_audio_generator
from pathlib import Path

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

    test = parallel_audio_generator.get_communicator(parallel_audio_generator.GenerationStatus.INIZIALIZING)

    path = Path("../data/models")
    generator = parallel_audio_generator.ParallelAudioGenerator(path, audio_settings, audio_model_settings, llm_settings)
    generator_channel = generator.get_generator_channel()
    generator._init_generation_process()
    while True:
        message = generator_channel.recv()
        print(parallel_audio_generator.communicator_to_string(message))
        if(message["status"] == parallel_audio_generator.GenerationStatus.WAITING_FOR_PROMPT):
            generator_channel.send("hello world")


if __name__ == '__main__':
    main()