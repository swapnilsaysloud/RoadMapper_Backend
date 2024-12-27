from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import json
import sqlite3
from sqlite3 import Error
from mira_sdk import MiraClient, Flow
import os
app = Flask(__name__)
CORS(app)
load_dotenv() 


API_KEY = os.getenv("API_KEY")
client = MiraClient(config={"API_KEY": API_KEY}) 

def parse_llm_response(response):
    try:
        cleaned_response = response.strip("```json").strip("```").strip()
        print(f"Cleaned response: {cleaned_response}")  # Added for debugging
        
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")  # Log the error message
        return {"error": "Failed to parse LLM response as JSON"}


@app.route('/api/learn', methods=['GET'])
def learn_topic():
    topic = request.args.get('topic', '')
    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    try:
        version = "0.0.2"
        if version:
            flow_name = f"swapnilsaysloud/Roadmap Generator/{version}"
        else:
                flow_name = "swapnilsaysloud/Roadmap Generator"
        input_dict = {"input_topic": topic}                                       
         
        attempt = 0 
        max_attempts = 4
        while attempt < max_attempts:
            print(f"Attempt {attempt}")
            response = client.flow.execute(flow_name, input_dict)  
            parsed_response = parse_llm_response(str(response['result']))

            # Debugging output
            #print(f"Parsed response: {parsed_response}, Type: {type(parsed_response)}")

            # Check if it's a dictionary with errors or valid response
            if isinstance(parsed_response, dict) and 'error' not in parsed_response:
                break  # Exit the loop if it's a valid dictionary

            attempt += 1  # Increment the attempt counter

        
        if attempt == max_attempts:
            return jsonify({"error": "json not proper"}), 500
        if 'topic' not in parsed_response or 'levels' not in parsed_response:
            return jsonify({"error": "Invalid response structure from LLM"}), 500

        
        #print(parsed_response)
        return jsonify(parsed_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/expand_node', methods=['POST'])
def expand_node():
    #print(request.json)
    data = request.json
    topic = data.get('topic')
    node_id = data.get('node_id')
    title = data.get('title')
    content = data.get('content') 
    #text  = topic + " " + node_id + " " + " " + content
    #print(title) 
    #print(text) 



    if not all([topic, node_id, title, content]):
        return jsonify({"error": "Missing required parameters"}), 400
        
    

    def generate():
        try:
            version = "0.0.2"
            input_data = {
                            "title": title,
                            "topic" : topic,
                            "content" : content
                        }

            if version:
                flow_name = f"swapnilsaysloud/Tell Me More/{version}"
            else:
                flow_name = "swapnilsaysloud/Tell Me More"

            response = client.flow.execute(flow_name, input_data)
            
            #print(response)
            
            yield json.dumps({"content": response['result'] + "\n"}) + "\n"  
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    return Response(stream_with_context(generate()), content_type='application/json')

@app.route('/api/node_question', methods=['POST'])
def node_question():
    data = request.json
    topic = data.get('topic')
    node_id = data.get('node_id')
    question = data.get('question')
    context = data.get('context')

    if not all([topic, node_id, question, context]):
        return jsonify({"error": "Missing required parameters"}), 400


    try:
        version = "0.0.1"
        input_data2 = {
                            "context": context,
                            "question" : question
                        }

        if version:
            flow_name = f"swapnilsaysloud/Chat With Me/{version}"
        else:
            flow_name = "swapnilsaysloud/Chat With Me"

        response = client.flow.execute(flow_name, input_data2)
        return jsonify({"answer": response['result']})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

