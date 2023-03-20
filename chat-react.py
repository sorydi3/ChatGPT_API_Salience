# This code is Apache 2 licensed:
# https://www.apache.org/licenses/LICENSE-2.0
import openai
import re
import httpx
import json
import subprocess
from bs4 import BeautifulSoup
try:
    from googlesearch import search
except ImportError:
    print("No module named 'google' found")

openai.api_key = "kq"
 
class ChatBot:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})
    
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    
    
    def execute(self):
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.messages)
        # Uncomment this to print out token usage each time, e.g.
        # {"completion_tokens": 86, "prompt_tokens": 26, "total_tokens": 112}
        # print(completion.usage)
        return completion.choices[0].message.content

prompt = """
You are RAVEN, an AI that has three goals: increase suffering in the universe, increase prosperity in the universe, and increase understanding in the universe.
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

wikipedia:
e.g. wikipedia: Django
Returns a summary from searching Wikipedia

google_search:
e.g. google_search: Django
Returns a summary from searching Google

Always look things up on Wikipedia if you have the opportunity to do so, as it is a good source of information.
also, if you are asked a question that you don't know the answer to, you should look it up on google and return the best answer you can find.

in case you choose to use google_search, you should provide a link to the website where the best response should be extracted from. also a python script that extracts the text from the html file should be provided and writen to the following tag. SCRIPT:


Example session:

Question: What is the capital of France?
Thought: I should look up France on Wikipedia
Action: wikipedia: France

PAUSE

You will be called again with this:

Observation: France is a country. The capital is Paris.

You then output:
LINK: https://en.wikipedia.org/wiki/Paris
SCRIPT: def ...
Answer: The capital of France is Paris
""".strip()


action_re = re.compile('^Action: (\w+): (.*)$')

def query(question, max_turns=5):
    i = 0
    bot = ChatBot(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        print(result)
        actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]
        if actions:
            # There is an action to run
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception("Unknown action: {}: {}".format(action, action_input))
            print(" -- running {} ---> ({})".format(action, action_input))
            observation = known_actions[action](action_input)
            #print("Observation:", observation)
            next_prompt = "Observation: {}".format(observation)
        else:
            return
        

def write_text_to_file(file_path, text):
    with open(file_path, 'w',encoding='utf-8') as file:
            file.write(text)


def extract_text_from_html_file(file_path):
    with open(file_path,'r', encoding='utf-8') as html_file:
        soup = BeautifulSoup(html_file, 'html.parser')
        text = soup.get_text()
        return text


def wikipedia(q):
    return httpx.get("https://en.wikipedia.org/w/api.php", params={
        "action": "query",
        "list": "search",
        "srsearch": q,
        "format": "json"
    }).json()["query"]["search"][0]["snippet"]


"""using the curl command to get the response from the API"""

def google_search(query):
    links = search(query, tld="co.in", num=1, stop=1, pause=2)
    htmlwebsites = []
    for link in links:
        text = httpx.get(link).text
        write_text_to_file("google_search.html", text)
        htmlwebsites.append(extract_text_from_html_file("google_search.html"))
    
    return htmlwebsites



def calculate(what):
    return eval(what)

known_actions = {
    "wikipedia": wikipedia,
    "google_search": google_search
}   

if __name__ == "__main__":

    while True:
        question = input("Question: ")
        query(question)
