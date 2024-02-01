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


def replace_keywords_with_int(text, replacement_keywords_number_mapping):
    if not all([text, replacement_keywords_number_mapping is not None]):
        raise ValueError("None arguments are not allowed")
    for keyword, number in replacement_keywords_number_mapping.items():
        text = text.replace(keyword, str(number))
    return text


def create_message_structure(**kwargs):
    role_system, role_user, number_sound_events, number_prompts = kwargs["role_system"], kwargs["role_user"], kwargs[
        "number_sound_events"], kwargs["number_prompts"]
    if not all([role_system, role_user, number_sound_events is not None, number_prompts is not None]):
        raise ValueError("None arguments are not allowed")
    replace_mapping = {"!NUMBER_SOUNDEVENTS": number_sound_events, "!NUMBER_PROMPTS": number_prompts}
    message_construct = [
        {"role": "system",
         "content": replace_keywords_with_int(role_system, replace_mapping)},
        {"role": "user", "content": replace_keywords_with_int(role_system, replace_mapping)}
    ]
    return message_construct


class LLMApiConnector:

    def __init__(self, api_key, **kwargs):
        self.client = OpenAI(api_key=api_key)
        model = kwargs.pop("model")
        if model is None:
            raise ValueError("model must not be None")
        self.model = model
        message_construct = create_message_structure(**kwargs)
        if message_construct is None:
            raise ValueError("message_construct must not be None")
        self.message_construct = message_construct

    def append_q_and_a_to_message_construct(self, q_and_a):
        copy_message_construct = self.message_construct.copy()
        copy_message_construct[1]["content"] += q_and_a
        return copy_message_construct

    def extract_prompts(self, q_and_a):
        messages = self.append_q_and_a_to_message_construct(q_and_a)
        try:
            completion = self.client.chat.completions.create(
                model=self.model, messages=messages, functions=[function_schema], function_call={"name": function_name})
            function_call = completion.choices[0].message.function_call
            json_output = json.loads(function_call.arguments)
            prompt_list = json_output.get("prompts", [])
        except Exception as e:
            raise e
        if prompt_list is None:
            raise ValueError("LLM did not return any prompts")
        return prompt_list
