import requests as requests
import os
from openai import OpenAI



client = OpenAI(api_key=api_key, base_url=base_url)


def SentLM_request(message, gpt_version):

    res = client.chat.completions.create(
        model=gpt_version,
        messages=message,
    )
    res_content = res.choices[0].message.content

    # print(res)
    return res_content
