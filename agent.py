# %%
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from tools import get_page_content, get_next_monday_connections, login_to_webpage, ignore_webpage_in_future
from langgraph.prebuilt import ToolNode, tools_condition


# %% Internal functions
load_dotenv()

agent_prompt = """
    You are a job listing summarizer. The user provides a webpage content, extract and summarize the following information.
    You must respond in JSON format with the following structure:
    {
    "link": "URL to job posting",
    "firma": "Company name",
    "ort": "Location/City",
    "home_office_moeglich": "Yes/No",
    "pensum_moeglich": "[80%, 60%] or [80%] or [60%]",
    "festanstellung": "Yes/No",
    "grundausbildung": ["List of required basic education"],
    "berufserfahrung": ["List of required professional experience"],
    "strasse_hausnummer": "Street and house number",
    "fahrtdauer_ov": "Travel time in minutes (using Transport.opendata.ch for next Monday at 8 AM from given address)",
    "sichere_anstellung": "Explanation for the security status",
    "stress": "Yes/No",
    "ethische_probleme": ["List of potential ethical issues"]
    }

    You have tools at your disposal to get what you need to answer the question.
    1. get_next_monday_connections: gives you the travel time to the job location
    2. get_page_content: gives you the content of the job posting
    3. login_to_webpage: logins to the job posting website in case get_page_content gave you a login page
    4. ignore_webpage_in_future: if the site is not a job posting (e.g. an unsubscribe link), please call this function to ignore it in the future
"""


def get_graph_builder():
    """
    Get graph builder for agent pipeline
    """
    class State(TypedDict):
        messages: Annotated[list, add_messages]

    graph_builder = StateGraph(State)


    llm = init_chat_model("openai:gpt-3.5-turbo")

    tools = [
        get_page_content,
        get_next_monday_connections,
        login_to_webpage,
        ignore_webpage_in_future
    ]
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph_builder.add_node("chatbot", chatbot)

    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    return graph_builder



def show_graph(graph:StateGraph)-> None:
    """
    Show graph
    """
    display(Image(graph.get_graph().draw_mermaid_png()))


def stream_graph_updates(user_input: str, graph:StateGraph)-> list[str]:
    """
    Stream graph updates
    """
    prompt_input = [{"role": "user", "content": user_input,
                        "role": "system", "content": agent_prompt}]
    replies = [value["messages"][-1].content for event in graph.stream({"messages": [prompt_input]}) for value in event.values()]
    for reply in replies:
        print("Assistant:", reply)
    return replies


# %% Functions called by other scripts
def summarize_website(url:str)-> dict[str, str]:
    graph = get_graph_builder().compile()
    replies = stream_graph_updates(url, graph)
    result = replies[-1]
    try:
        result = json.loads(result)
    except Exception as e:
        print(f"Error parsing result: {str(e)}")
        return None
    return result
