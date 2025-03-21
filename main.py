import json
import os
import time
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import custom_functions
from waitress import serve

# Check OpenAI version compatibility
from packaging import version

required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

if current_version < required_version:
  raise ValueError(
      f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
  )
else:
  print("OpenAI version is compatible.")

# Create Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    default_headers={"OpenAI-Beta": "assistants=v2"}
)
assistant = client.beta.assistants.create

# Create or load assistant
assistant_id = custom_functions.create_assistant(
    client)  # this function comes from "functions.py"


# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
  print("Starting a new conversation...")
  thread = client.beta.threads.create()
  print(f"New thread created with ID: {thread.id}")
  return jsonify({"thread_id": thread.id})


# Generate response
@app.route('/chat', methods=['POST'])
def chat():
  data = request.json
  thread_id = data.get('thread_id')
  user_input = data.get('message', '')

  if not thread_id:
    print("Error: Missing thread_id")
    return jsonify({"error": "Missing thread_id"}), 400

  print(f"Received message: {user_input} for thread ID: {thread_id}")

  # Add the user's message to the thread
  client.beta.threads.messages.create(thread_id=thread_id,
                                   role="user",
                                   content=user_input)

  # Run the Assistant
  run = client.beta.threads.runs.create(thread_id=thread_id,
                                     assistant_id=assistant_id)

  # Check if the Run requires action (function call)
  while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                run_id=run.id)
    if run_status.status == 'completed':
      break
    elif run_status.status == 'requires_action':
      # Handle the function call
      for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "create_lead":
          # Process lead creation
          arguments = json.loads(tool_call.function.arguments)
          name = arguments.get('name','')
          email = arguments.get('geburtsdatum','')
          geburtsdatum = arguments.get('email','')
          sf_klasse = arguments.get('sf_klasse','')
          hsn_tsn_nummer = arguments.get('hsn_tsn_nummer','')
          marke = arguments.get('marke','')
          model = arguments.get('model','')
          katagorie = arguments.get('katagorie','')
          leistung_ps = arguments.get('leistung_ps','')
          baujahr = arguments.get('baujahr','')
          hubraum = arguments.get('hubraum','')
          jaehrliche_fahrleistung = arguments.get('jaehrliche_fahrleistung','')

          output = custom_functions.create_lead(name, email, geburtsdatum, sf_klasse, hsn_tsn_nummer, marke, model, katagorie, leistung_ps, baujahr, hubraum, jaehrliche_fahrleistung)
          client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                    run_id=run.id,
                                                    tool_outputs=[{
                                                        "tool_call_id": tool_call.id,
                                                        "output": json.dumps(output)
                                                    }])
      time.sleep(1)

  # Retrieve and return the latest message from the assistant
  messages = client.beta.threads.messages.list(thread_id=thread_id)
  response = messages.data[0].content[0].text.value

  print(f"Assistant response: {response}")
  return jsonify({"response": response})


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080)