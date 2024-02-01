from openai import OpenAI
import json

function_name = "formatAsJson"

function_schema = {
    "name": function_name,
    "parameters": {
        "type": "object",
        "properties": {
            "prompts": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },
        "required": ["prompts"]
    }
}

file = open("QA.txt")
qua = file.read()

llm_settings = {
    "number_sound_events": 4,
    "number_prompts": 10,
    "role_system": "Your are an intelligent system that extracts prompts from a questionnaire to be used with a generative ai model. Your primary role is to analyze and interpret the responses to this questionnaire, which is focused on eliciting detailed descriptions of personal memories that users wish to re-experience through audio. From the user's descriptions, you will identify and extract !NUMBER_SOUNDEVENTS key sound events that are pivotal to each memory. For each identified sound event, you are tasked with generating !NUMBER_PROMPTS distinct but closely related prompts. These prompts will be used by a generative AI model to create audio files that encapsulate the essence of the sound events. The challenge lies in ensuring that each set of prompts remains true to the core idea of its corresponding sound event, while introducing subtle variations to offer a range of auditory experiences. This process aims to recreate a multi-faceted and immersive auditory representation of the user's cherished memories.",
    "role_user":  "Please extract !NUMBER_SOUNDEVENTS key sound events from the following Q&A and generate !NUMBER_PROMPTS prompts for each sound event. The Q&A is focused on eliciting detailed descriptions of personal memories that users wish to re-experience through audio. The prompts will be used by a generative AI model to create audio files that encapsulate the essence of the sound events. Please ensure that each set of prompts remains true to the core idea of its corresponding sound event, while introducing subtle variations to offer a range of auditory experiences. Do not use verbs like create, generate, synthesize ... but rather just describe the audio and the scene. \n Q&A: \n",
    "model": "gpt-4-1106-preview"
}

def fill_replacement_with_int(text, replacement_keyword, number):
    return text.replace(replacement_keyword, str(number))

def create_message_construct(**kwargs):
    role, user, number_sound_events, number_prompts = kwargs["role_system"], kwargs["role_user"], kwargs["number_sound_events"], kwargs["number_prompts"]
    message_construct = [
       {"role": "system", "content": fill_replacement_with_int(role, "!NUMBER_SOUNDEVENTS", number_sound_events)},
       {"role": "user", "content": fill_replacement_with_int(user, "!NUMBER_PROMPTS", number_prompts)}
    ]
    return message_construct


def append_q_and_a_to_message_construct(message_construct, q_and_a):
    copy_message_construct = message_construct.copy()
    copy_message_construct[1]["content"] += q_and_a
    return copy_message_construct


class LLMApiConnector:

    def __init__(self, apikey, **kwargs):
        self.client = OpenAI(api_key=apikey)
        self.message_construct = create_message_construct(**kwargs)

    def extract_prompts(self, q_and_a, **llm_settings):
        messages_construct = create_message_construct(**llm_settings)
        messages = append_q_and_a_to_message_construct(messages_construct, q_and_a)
        completion = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            functions=[function_schema],
            function_call={"name": function_name}
        )

        # Retrieve the function call from the response
        function_call = completion.choices[0].message.function_call

        # Parse the arguments as JSON
        json_output = json.loads(function_call.arguments)

        # convert the prompts to a list of lists
        python_list = json_output.get("prompts", [])
        return python_list





def main():
    llm = LLMApiConnector("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", **llm_settings)
    list_prompts = llm.extract_prompts(qua, **llm_settings)
    print(list_prompts)


if __name__ == "__main__":
    main()


