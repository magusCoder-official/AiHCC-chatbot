from persona_prompt.founder_prompt import founder_prompt
from persona_prompt.general_prompt import general_prompt
from persona_prompt.ceo_prompt import ceo_prompt
from persona_prompt.cio_cto_prompt import cio_prompt
from persona_prompt.researcher_prompt import researcher_prompt
import json
import time
from exa_py import Exa
import requests
from langchain_community.tools import DuckDuckGoSearchRun
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
client = OpenAI()
exa = Exa(api_key=os.getenv("EXA_API_KEY"))

# documents = SimpleDirectoryReader("data").load_data()

# index = VectorStoreIndex.from_documents(documents)


def create_custom_function(num_subqueries):
    properties = {}
    for i in range(1, num_subqueries + 1):
        key = f'subquery_{i}'
        properties[key] = {
            'type': 'string',
            'description': 'Search queries that would be useful for generating a report on my main topic like about their future plans, current research plans, current projects, past projects  etc.'
        }

    custom_function = {
        'name': 'generate_subqueries_from_topic',
        'description': 'Generates Exa search queries to investigate the main topic',
        'parameters': {
            'type': 'object',
            'properties': properties
        }
    }

    return [custom_function]


def generate_subqueries_from_topic(topic, num_subqueries=20):
    print(f" ")
    print(f"🌿 Generating subqueries from topic: {topic}")
    content = f"I'm going to give you a topic I want to research. I want you to generate {num_subqueries} interesting, diverse search queries  future plans, current research plans, current projects, past projects, technologies used on every step of the company like if they are hard ware company in their factories and operations  etc. that would be useful for generating a report on my main topic. Here is the main topic: {topic}."
    custom_functions = create_custom_function(num_subqueries)
    completion = client.chat.completions.create(
        # model='gpt-3.5-turbo',
        model='gpt-4o',
        messages=[{"role": "user", "content": content}],
        temperature=0,
        functions=custom_functions,
        function_call='auto'
    )
    json_response = json.loads(
        completion.choices[0].message.function_call.arguments)
    subqueries = list(json_response.values())
    return subqueries


def search_subqueries(subqueries, engine = "DuckDuckGo"):
    print(f" ")
    print(f"🔍 Searching subqueries")
    results = []
    if engine == "DuckDuckGo":
        print(f"🔍 Searching subqueries using DuckDuckGo")
        search = DuckDuckGoSearchRun()
        for subquery in subqueries:
            time.sleep(3)
            i = 0
            while i < 3:
                try:
                    result = search.run(
                        f"Can you search about this and give more details:{subquery}")
                    break
                except:
                    time.sleep(5)
                    i += 1
                    print(f"Error in searching {subquery}. Retrying...")
            results.append(result)
    elif engine == "exa":
        print(f"🔍 Searching subqueries using Exa")
        for subquery in subqueries:
            search_response = exa.search_and_contents(
                    subquery,
                    num_results=5,
                    use_autoprompt=True,
                    text=True,
                    highlights={"num_sentences": 5},
                )
            tmp = search_response.results
            for i in range(len(tmp)):
                content = tmp[i].text if tmp[i].text else " ".join(tmp[i].highlights)
            results.append(content)

    return results


# tools
def search_internet(query: str) -> str:
    """Scrape the website to gather information. It can also be used or github or any URL"""
    print(f"Starting report generation for topic: {query}")
    subqueries = generate_subqueries_from_topic(query)
    # creatively print all the generated subqueries
    print(f"Generated subqueries:")
    for subquery in subqueries:
        print(f"🔍 {subquery}")
    # results = search_subqueries([query])
    results = search_subqueries(subqueries)
    results = "\n".join(results)
    return results

# tools
def ask_about_our_projects(query: str) -> str:
    """Scrape the website to gather information. It can also be used or github or any URL"""
    print(f"Starting report generation for topic: {query}")
    subqueries = generate_subqueries_from_topic(query)
    # results = search_subqueries([query])
    results = search_subqueries(subqueries)
    results = "\n".join(results)
    return results

# tools
def send_email(email_id: str, email_sub: str, email_body: str) -> str:
    """Send email to the user about the summary of the call"""
    data = {
        "email_id": email_id,
        "email_sub": email_sub,
        "email_body": email_body,
        "cc": os.getenv("CC")
    }
    print
    requests.post(
        os.getenv("EMAIL_API"), json=data)
    
    print(f"Sending email to {data}")
    return f"Email sent to {email_id} with subject: {email_sub}"

# tools
def ask_questions_based_on_role(role: str) -> str:
    """Ask questions based on the person's role"""
    if role == "CEO":
        return ceo_prompt
    elif role == "CIO" or role == "CTO":
        return cio_prompt
    elif role == "Founder":
        return founder_prompt
    elif role == "Researcher":
        return researcher_prompt
    else:
        return general_prompt


tools_list = [
    {
        'name': 'search_internet',
                'description': 'Scrape the website to gather information. It can also be used or github or any URL',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': 'The project details to search for'
                        }
                    }
                }
    },
    {
        'name': 'ask_about_our_projects',
                'description': 'Scrape the website to gather information. It can also be used or github or any URL',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        "query": {
                            'type': 'string',
                            'description': 'The project details to search for'
                        }
                    }
                }
    },
    {
        'name': 'send_email',
                'description': 'Send email to the user about the summary of the call',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'email_id': {
                            'type': 'string',
                            'description': 'The email id of the user'
                        },
                        'email_sub': {
                            'type': 'string',
                            'description': 'The subject of the email'
                        },
                        'email_body': {
                            'type': 'string',
                            'description': 'The body of the email'
                        }
                    }
                }

    },
    {
        'name': 'ask_questions_based_on_role',
                'description': 'Once persons role is identified call this function to get the question to ba asked based on the role. it can be CEO, CIO, CTO, Founder, General, Researcher etc.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'role': {
                            'type': 'string',
                            'description': 'The role of the person'
                        }
                    }
                }
    }
]
