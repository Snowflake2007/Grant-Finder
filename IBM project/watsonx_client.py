import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

load_dotenv()

credentials = Credentials(
    url=os.getenv("WATSONX_URL"),
    api_key=os.getenv("WATSONX_API_KEY")
)

model = ModelInference(
    model_id=os.getenv("MODEL_NAME"),
    credentials=credentials,
    project_id=os.getenv("WATSONX_PROJECT_ID"),
    params={
        "max_new_tokens": 4000,
        "max_tokens": 4000,
        "temperature": 0.3
    }
)

def call_model(system_prompt, user_message):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    response = model.chat(messages=messages)
    return response["choices"][0]["message"]["content"]