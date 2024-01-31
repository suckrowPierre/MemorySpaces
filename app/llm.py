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


def fill_replacement_with_int(text, replacement_keyword, number):
    return text.replace(replacement_keyword, str(number))


def create_message_construct(**kwargs):
    role, user, number_sound_events, number_prompts = kwargs["role"], kwargs["user"], kwargs["number_sound_events"], kwargs["number_prompts"], kwargs["model"]
    message_construct = [
       {"role": "system", "content": fill_replacement_with_int(role, "!NUMBER_SOUNDEVENTS", number_sound_events)},
       {"role": "user", "content": fill_replacement_with_int(user, "!NUMBER_PROMPTS", number_prompts)}, 
    ] 
    return message_construct



class LLMAPI:
    def __init__(self, apikey, **kwargs):
        self.model = kwargs.pop("model")
        self.client = OpenAI(apikey)
        self.message_construct = create_message_construct(**kwargs)

    def append_q_and_a_to_message_construct(self, q_and_a):
        copy_message_construct = self.message_construct.copy()
        copy_message_construct[1]["content"] += q_and_a
        return copy_message_construct

    def extractPrompts(self, q_and_a):
        messages = self.append_q_and_a_to_message_construct(q_and_a)
        completion = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        functions=[function_schema],
        function_call={"name": function_name})
        function_call = completion.choices[0].message.function_call
        json_output = json.loads(function_call.arguments)
        python_list = json_output.get("prompts", [])
        return python_list

