import new_LLM
from dotenv import load_dotenv
import os


llm_settings = {
    "number_sound_events": 4,
    "number_prompts": 10,
    "role_system": "Your are an intelligent system that extracts prompts from a questionnaire to be used with a generative ai model. Your primary role is to analyze and interpret the responses to this questionnaire, which is focused on eliciting detailed descriptions of personal memories that users wish to re-experience through audio. From the user's descriptions, you will identify and extract !NUMBER_SOUNDEVENTS key sound events that are pivotal to each memory. For each identified sound event, you are tasked with generating !NUMBER_PROMPTS distinct but closely related prompts. These prompts will be used by a generative AI model to create audio files that encapsulate the essence of the sound events. The challenge lies in ensuring that each set of prompts remains true to the core idea of its corresponding sound event, while introducing subtle variations to offer a range of auditory experiences. This process aims to recreate a multi-faceted and immersive auditory representation of the user's cherished memories.",
    "role_user":  "Please extract !NUMBER_SOUNDEVENTS key sound events from the following Q&A and generate !NUMBER_PROMPTS prompts for each sound event. The Q&A is focused on eliciting detailed descriptions of personal memories that users wish to re-experience through audio. The prompts will be used by a generative AI model to create audio files that encapsulate the essence of the sound events. Please ensure that each set of prompts remains true to the core idea of its corresponding sound event, while introducing subtle variations to offer a range of auditory experiences. Do not use verbs like create, generate, synthesize ... but rather just describe the audio and the scene. \n Q&A: \n",
    "model": "gpt-4-1106-preview"
}

def main():
    file = open("QA.txt")
    qa = file.read()

    load_dotenv()
    api_key = os.getenv("LLM_API_KEY")
    llm=new_LLM.LLMApiConnector(api_key, **llm_settings)
    list_prompts = llm.extract_prompts(qa)
    print(list_prompts)

if __name__ == "__main__":
    main()
