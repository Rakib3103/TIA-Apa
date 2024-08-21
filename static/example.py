from openai import OpenAI

client = OpenAI(api_key="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")

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a haiku about recursion in programming."}
    ]
)

print(completion.choices[0].message['content'])
