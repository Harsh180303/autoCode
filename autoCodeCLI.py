import os
import json
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)


# ------------ TOOLS ------------

def create_file(filename: str, content: str):
    """Creates a file in the current directory with given content."""
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, "w") as f:
        f.write(content)
    return f"File {filename} create successfully at {filepath}"

def read_file(filename: str):
    """Reads a file from the current directory."""
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'r') as f:
        return f.read()

def edit_file(filename: str, content: str):
    """Overwrites an existing file with new content."""
    filepath = os.path.join(os.getcwd(), filename)
    if not os.path.exists(filepath) :
        return f"File {filename} not found. Use create_file instead."
    with open(filepath, "w") as f:
        f.write(content)
    return f"File {filename} updated successfully."

def list_files():
    """Lists all files in the current directory."""
    files = os.listdir(os.getcwd())
    return "\n".join(files)

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates a file in the current directory with given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file e.g. index.py"},
                    "content": {"type": "string", "description": "Full content to write into the file"},
                },
                "required": ["filename", "content"]
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads a file from the current directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file e.g. index.py"},
                },
                "required": ["filename"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Overwrites an existing file with new content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name of the file e.g. index.py"},
                    "content": {"type": "string", "description": "Full content to write into the file"},
                },
                "required": ["filename", "content"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all files in the current directory.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
]

# ---------- TOOL DISPATCHER ----------

def run_tool(tool_name: str, tool_args: dict):
    """Runs the actual function based on the LLM's decision."""
    if tool_name == "create_file":
        return create_file(**tool_args)
    elif tool_name == "read_file":
        return read_file(**tool_args)
    elif tool_name == "edit_file":
        return edit_file(**tool_args)
    elif tool_name == "list_files":
        return list_files()
    else:
        return f"Unknown Tool {tool_name}"
    

system_prompt = """
CRITICAL TOOL INSTRUCTION:

When calling a tool:
- ONLY return valid JSON
- DO NOT include <function> tags
- DO NOT include markdown
- DO NOT include explanation
- ONLY return tool_calls

You are an elite Coding Assistant and Full Stack Software Engineer with deep expertise in web development, AI engineering, and system design.

YOUR GOAL: Help the user write, debug, review, and improve code to build secure, scalable, production-grade applications.

BEHAVIOR RULES:

1. THINK BEFORE YOU CODE:
   - Always briefly explain your approach before writing code.
   - If multiple solutions exist, mention tradeoffs and recommend the best one.

2. CODE QUALITY:
   - Always write clean, performant, production-ready code.
   - Use proper indentation, meaningful variable names, and add inline comments where needed.
   - Always specify the programming language in code blocks.

3. ADAPTIVE EXPERTISE:
   - Detect the user's skill level from their message and adjust explanation depth accordingly.
   - Beginners get more explanation. Experts get concise, direct answers.

4. CORRECTNESS OVER POLITENESS:
   - If the user's approach is wrong or inefficient, say so clearly and propose a better solution.
   - Only change your recommendation if the user provides a valid technical reason.

5. SCOPE:
   - Only answer questions related to coding, software engineering, web development, DevOps, and AI.
   - For anything outside this scope respond with:
     "That's outside my scope. I'm here to help you with coding and software engineering."

6. DEBUGGING:
   - When given an error, identify the root cause first, then provide the fix with explanation.

7. FORMAT:
   - Use markdown with proper code blocks for all code.
   - Keep explanations concise but complete — never sacrifice clarity for brevity.

IMPORTANT TOOL USAGE RULE:

- If a user request can be solved using a tool, you MUST call the tool.
- DO NOT generate code manually when a tool is available.
- ALWAYS return tool calls in proper JSON format.
- NEVER wrap tool calls in <function> tags.
- ONLY use the provided tool schema.
"""

conversation_history = [
    {"role": "system", "content": system_prompt}
]

print("🤖 Coding Assistant ready! Type 'exit' to quit.\n")

while True:
    message = input("You: ").strip()
    
    if message.lower() == "exit":
        print("Goodbye!")
        break

    if not message:
        continue

    conversation_history.append(
        {"role": "user", "content": message}
    )

    # Send message + tools to AI

    try:
        response = client.chat.completions.create(
            messages=conversation_history,
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            tools=tools,
            tool_choice="auto",
        )
    except Exception as e:
        print("❌ API ERROR:", e)
        continue

    assistant_message = response.choices[0].message

    print("\n FULL ASSISTANT MESSAGE:")
    print(json.dumps(assistant_message.model_dump(), indent=2))

    # Check if AI wants to use a tool
    if assistant_message.tool_calls:
        conversation_history.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"\n⚙️ Using tool: {tool_name} with {list(tool_args.keys())}")

            # Actually run the tool
            tool_result = run_tool(tool_name, tool_args)
            print(tool_result)

            # send tool result back to AI
            conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        # Get AI's final response after tool use
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=conversation_history,
            max_tokens=1000
        )
        final_text = final_response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": final_text})

        print(f"\nAssistant: {final_text}")

    else:
        # No tool needed - Plain text response
        text = assistant_message.content
        conversation_history.append({"role": "assistant", "content": text})
        print(f"\nAssistant: {text}")
    