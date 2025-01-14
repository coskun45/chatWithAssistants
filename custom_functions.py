import json
import requests
import os
from openai import OpenAI
from assistant_insturctions import assistant_instructions
from dotenv import load_dotenv, dotenv_values

load_dotenv()

# Init OpenAI Client
client = OpenAI()

# Add lead to Airtable
def create_lead(name="",geburtsdatum="", email="",sf_klasse="",hsn_tsn_nummer="",marke="", model="", katagorie="", leistung_ps="", baujahr="", hubraum="",jaehrliche_fahrleistung=""):
                            
  url = "https://api.airtable.com/v0/appzBpuPlOsfS0zvT/Leads"  # Change this to your Airtable API URL
  headers = {
      "Authorization" : 'Bearer ' + dotenv_values().get("AIRTABLE_API_KEY"),
      "Content-Type": "application/json"
  }
  data = {
      "records": [{
          "fields": {
            "Name": name,
            "Geburtsdatum": geburtsdatum,
            "Email": email,
            "Sf_klasse": sf_klasse,
            "Hsn_tsn_nummer": hsn_tsn_nummer,
            "Marke": marke,
            "Model": model,
            "Kategorie": katagorie,
            "Leistung_ps": leistung_ps,
            "Baujahr": baujahr,
            "Hubraum": hubraum,
            "Jaehrliche_fahrleistung": jaehrliche_fahrleistung
              
          }
      }]
  }
  response = requests.post(url, headers=headers, json=data)
  if response.status_code == 200:
    print("Lead created successfully.")
    return response.json()
  else:
    print(f"Failed to create lead: {response.text}")


# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    # To change the knowledge document, modifiy the file name below to match your document
    # If you want to add multiple files, paste this function into ChatGPT and ask for it to add support for multiple files
    file = client.files.create(file=open("Versicherungsgrundlagen_KFZ.docx", "rb"),
                               purpose='assistants')

    assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file, edit on left panel if you want to change the prompt
        instructions=assistant_instructions,
        model="gpt-4-turbo",
        tools=[
            {
                "type":"file_search"
            },
            
            {
                "type": "function",  # Adds the lead capture as a tool
                "function": {
                    "name": "create_kfz_insurance_lead",
                    "description": "Capture KFZ insurance lead details and save to Airtable.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The full name of the customer. Example: 'John Doe'."
                            },
                            "geburtsdatum": {
                                "type": "string",
                                "description": "The date of birth of the customer in the format YYYY-MM-DD. Example: '1990-05-20'."
                            },
                            "email": {
                                "type": "string",
                                "description": "Email of the lead. Example: 'example@gmail.com'"
                            },
                            "sf_klasse": {
                                "type": "string",
                                "description": "The SF class of the customer. Example: 'SF 10'."
                            },
                            "hsn_tsn_nummer": {
                                "type": "string",
                                "description": "The HSN/TSN number of the vehicle. Example: '0603/BAU'."
                            },
                            "marke": {
                                "type": "string",
                                "description": "The brand of the car. Example: 'Volkswagen'."
                            },
                            "model": {
                                "type": "string",
                                "description": "The model of the car. Example: 'Golf 7'."
                            },
                            "kategorie": {
                                "type": "string",
                                "description": "The category of the car (e.g., Van/Bus, Kombi/Limousine). Example: 'Kombi'."
                            },
                            "leistung_ps": {
                                "type": "integer",
                                "description": "The power of the car in PS (horsepower). Example: 150."
                            },
                            "baujahr": {
                                "type": "integer",
                                "description": "The year the car was manufactured. Example: 2018."
                            },
                            "hubraum": {
                                "type": "integer",
                                "description": "The engine capacity of the car in cm³. Example: 1998."
                            },
                            "jaehrliche_fahrleistung": {
                                "type": "integer",
                                "description": "The annual mileage of the car in kilometers. Example: 15000."
                            }
                        },
                        "required": [
                            "name",
                            "geburtsdatum",
                            "sf_klasse",
                            "hsn_tsn_nummer",
                            "marke",
                            "model",
                            "kategorie",
                            "leistung_ps",
                            "baujahr",
                            "hubraum",
                            "jaehrliche_fahrleistung"
                        ]
                    }
                }
            }
        ],
        tool_resources={
                "file_search":
                {
                    "vector_stores": [{"file_ids":[file.id]}]
                }
            }
        )

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id