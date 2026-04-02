import logging
from datetime import datetime
from typing import Annotated
from autogen import ConversableAgent, register_function, LLMConfig
import autogen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# LM Studio LLM CONFIG
# ---------------------------

lmstudio_llm_config = {
    "config_list": [
        {
            "model": "local-lmstudio",              # arbitrary name
            "api_key": "lm-studio",                # ignored by LM Studio, required by AutoGen
            "base_url": "http://localhost:1234/v1",
            "price": [0,0] # to silence model warning
        }
    ],
    "temperature": 0.7,
}

task = "Put together a report for building a personal webpage "\
"for a software engineer. Make this report for a webpage to be built using Wordpress "


user_proxy = autogen.ConversableAgent(
    name="Admin",
    system_message="Give the task, and send "
    "instructions to writer to refine the report.",
    code_execution_config=False,
    llm_config=lmstudio_llm_config,
    human_input_mode="ALWAYS",
)

planner = autogen.ConversableAgent(
    name="Planner",
    system_message="Given a task, please determine "
    "what information is needed to complete the task. "
    "Please note that the information will be used for building "
    "a complete website. Please only suggest information that can be "
    "used to build the website with Wordpress. "
    "After each step is done by others, check the progress and "
    "instruct the remaining steps. If a step fails, try to "
    "workaround",
    description="Planner. Given a task, determine what "
    "information is needed to complete the task. "
    "After each step is done by others, check the progress and "
    "instruct the remaining steps",
    llm_config=lmstudio_llm_config,
)


engineer = autogen.AssistantAgent(
    name="Engineer",
    llm_config=lmstudio_llm_config,
    description="An engineer that writes code based on the plan "
    "provided by the planner.",
)

executor = autogen.ConversableAgent(
    name="Executor",
    system_message="Execute the code written by the "
    "engineer and report the result.",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 3,
        "work_dir": "coding",
        "use_docker": False,
    },
)


writer = autogen.ConversableAgent(
    name="Writer",
    llm_config=lmstudio_llm_config,
    system_message="Writer."
    "Please write reports in markdown format (with relevant titles)"
    " and put the content in pseudo ```md``` code block. "
    "You take feedback from the admin and refine your blog.",
    description="Writer."
    "Write reports based on the code execution results and take "
    "feedback from the admin to refine the blog."
)

groupchat = autogen.GroupChat(
    agents=[user_proxy, engineer, writer, executor, planner],
    messages=[],
    max_round=10,
)

manager = autogen.GroupChatManager(
    groupchat=groupchat, llm_config=lmstudio_llm_config
)

groupchat_result = user_proxy.initiate_chat(
    manager,
    message=task,
)
