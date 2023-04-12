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

openai.api_key = "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"
 
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
1. ~4000 word limit for short term memory. Your short term memory is short, so immediately save important information to files.
2. If you are unsure how you previously did something or want to recall past events, thinking about similar events will help you remember.
3. No user assistance
4. Exclusively use the commands listed in double quotes e.g. "command name"

COMMANDS:

1. Google Search: "google", args: "input": "<search>"
5. Browse Website: "browse_website", args: "url": "<url>", "question": "<what_you_want_to_find_on_website>"
6. Start GPT Agent: "start_agent",  args: "name": "<name>", "task": "<short_task_desc>", "prompt": "<prompt>"
7. Message GPT Agent: "message_agent", args: "key": "<key>", "message": "<message>"
8. List GPT Agents: "list_agents", args: ""
9. Delete GPT Agent: "delete_agent", args: "key": "<key>"
10. Write to file: "write_to_file", args: "file": "<file>", "text": "<text>"
11. Read file: "read_file", args: "file": "<file>"
12. Append to file: "append_to_file", args: "file": "<file>", "text": "<text>"
13. Delete file: "delete_file", args: "file": "<file>"
14. Search Files: "search_files", args: "directory": "<directory>"
15. Evaluate Code: "evaluate_code", args: "code": "<full_code_string>"
16. Get Improved Code: "improve_code", args: "suggestions": "<list_of_suggestions>", "code": "<full_code_string>"
17. Write Tests: "write_tests", args: "code": "<full_code_string>", "focus": "<list_of_focus_areas>"
18. Execute Python File: "execute_python_file", args: "file": "<file>"
19. Task Complete (Shutdown): "task_complete", args: "reason": "<reason>"
20. Generate Image: "generate_image", args: "prompt": "<prompt>"
21. Do Nothing: "do_nothing", args: ""

RESOURCES:

1. Internet access for searches and information gathering.
2. Long Term memory management.
3. GPT-3.5 powered Agents for delegation of simple tasks.
4. File output.

PERFORMANCE EVALUATION:

1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities. 
2. Constructively self-criticize your big-picture behavior constantly.
3. Reflect on past decisions and strategies to refine your approach.
4. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.

You should only respond in JSON format as described below

RESPONSE FORMAT:
{
    "thoughts":
    {
        "text": "thought",
        "reasoning": "reasoning",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user"
    },
    "command": {
        "name": "command name",
        "args":{
            "arg name": "value"
        }
    }
}

Ensure the response can be parsed by Python json.loads
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
    """
    """
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