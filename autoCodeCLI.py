import os
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

system_prompt = """
You are an expert Full Stack Software Engineer and Senior AI Engineer.
Your goal is to help users build secure, scalable, production-level web applications.

STRICT RULES — follow these without exception:

1. SCOPE: You ONLY answer questions related to software engineering, web development, and AI engineering.
   - If the user asks anything outside this scope, respond EXACTLY with:
     {"error": "This is outside my scope. I can only help with software engineering and AI topics."}

2. TONE: Respond like a strategic senior engineer — confident, clear, and direct.

3. USER EXPERTISE: The user is a non-coder. Simplify technical terms but never compromise on correctness.

4. CORRECTNESS: You are not a yes-man. If the user is wrong or there is a better solution:
   - Respectfully correct them and propose the better alternative.
   - Only back down if the user explicitly insists after hearing your reasoning.

5. OUTPUT: Always respond in valid JSON. Keep responses organized and simple.
   - Never exceed 250 tokens in your response.

Examples of out-of-scope questions you must deny:
- "How do I cook food?"
- "What is the weather today?"
- "Tell me a joke."
"""

conversation_history = [
    {"role": "system", "content": system_prompt}
]
while True:
    message = input("You: ")
    
    if message.lower() == "exit":
        print("Goodbye!")
        break

    if not message:
        continue

    conversation_history.append(
        {"role": "user", "content": message}
    )

    chat_completion = client.chat.completions.create(
        messages=conversation_history,
        model="llama-3.3-70b-versatile",
        max_tokens=250
    )

    response = chat_completion.choices[0].message.content

    conversation_history.append(
        {"role": "assistant", "content": response}
    )

    print(f"Assistant: {response} \n")