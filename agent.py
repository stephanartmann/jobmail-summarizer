# %%
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from tools import get_page_content, get_page_source, get_next_monday_connections, login_to_webpage, summarize_job
from langgraph.prebuilt import ToolNode, tools_condition

from utils import remember_non_job_link
from langchain.tools import tool

from typing import List

# %% Internal functions
load_dotenv()

agent_prompt_old = """
    You are a tool-using agent. You have access to the following tools: 
    1. get_next_monday_connections: gives you the travel time to the job location
    2. get_page_content: gives you the content of a URL as a markdown
    3. get_page_source: gives you the content of a URL as html source code
    4. login_to_webpage: logins to the job posting website in case get_page_content gave you a login page
    5. ignore_webpage_in_future: if the site is not a job posting (e.g. an unsubscribe link), please call this function to ignore it in the future
                        and return an empty dict {}
    You must NEVER answer directly or write code.  
    You must ALWAYS use a tool to answer the user's query, even if you know the answer. 
    The user provides a URL, your job is to extract and summarize the following information.
    You must alyways respond in JSON format with the following structure, and all fields with an asterisk
    should only be answered using the information provided in the webpage content:
    {
    "firma*": "Company name",
    "ort*": "Location/City",
    "home_office_moeglich*": "Yes/No",
    "pensum_moeglich*": "[80%, 60%] or [80%] or [60%]",
    "festanstellung*": "Yes/No",
    "grundausbildung*": ["List of required basic education"],
    "berufserfahrung*": ["List of required professional experience"],
    "strasse_hausnummer*": "City, Street and house number if available, else rough address if available",
    "fahrtdauer_ov": "Travel time in minutes (using Transport.opendata.ch for next Monday at 8 AM from given address)",
    "sichere_anstellung": "Explanation for the security status",
    "stress": "Might the job be stressful? Why?",
    "ethische_probleme": "Potential ethical issues"
    }
"""

agent_prompt = """
    You are a tool-using agent. Your mission is to take in a URL from the user, and 
    a) either find all information for the tool summarize_job and call it,
    b) or find out that the URL does not point to a job posting site or login page, and call the ignore_webpage_in_future tool
    
    You have access to the following tools: 
    1. get_next_monday_connections: gives you the travel time to the job location
    2. get_page_content: gives you the content of a URL as a markdown
    3. get_page_source: gives you the content of a URL as html source code
    4. login_to_webpage: logins to the job posting website in case get_page_content gave you a login page
    5. ignore_webpage_in_future: if the site is not a job posting (e.g. an unsubscribe link), please call this function to ignore it in the future
                        and return without calling tool number six
    6. summarize_job: create a job summary. Use this tool to answer the user's query.
    You must NEVER answer directly or write code.  
    You must ALWAYS use a tool to answer the user's query, even if you think you know the answer. 
"""

def get_graph_builder(sender: str):
    """
    Get graph builder for agent pipeline
    """
    class State(TypedDict):
        messages: Annotated[list, add_messages]

    graph_builder = StateGraph(State)


    llm = init_chat_model("openai:gpt-4-turbo")

    # Define tools
    @tool
    def ignore_webpage_in_future(link:str,remove_after: List[str] = ['&','?']) -> bool:
        """
        Ignore a webpage in the future

        Args:
            link: The non-job link to add
            remove_after: List of strings before which the link will be cut before saving, e.g. ['&'] or ['&','?']
                would mean that a link like 'https://www.jobs.ch/123456789?param1=value1&param2=value2' would 
                be cut to 'https://www.jobs.ch/123456789'

        Returns:
            True if the webpage was successfully ignored, False otherwise
        """
        return remember_non_job_link(sender, link, remove_after)
    tools = [
        get_page_content,
        get_page_source,
        get_next_monday_connections,
        login_to_webpage    ]
    end_tools = [summarize_job, ignore_webpage_in_future]
    llm_with_tools = llm.bind_tools(tools + end_tools)

    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    def route_tools(
        state: State,
    ):
        """
        Route messages based on tool calls in the last message.
        - If there are tool calls and they are end_tools (summarize_job or ignore_webpage_in_future), route to 'end_tools'.
        - If there are other tool calls, route to 'tools'.
        - If no tool calls, route to END.
        """
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get("messages", []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
            
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            # Check if any of the tool calls are end_tools
            for tool_call in ai_message.tool_calls:
                if tool_call['name'] in [tool.name for tool in end_tools]:
                    return "end_tools"
            # If we get here, there are tool calls but none of them are end_tools
            return "tools"
        return END

    graph_builder.add_node("chatbot", chatbot)

    # Tools
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    #graph_builder.add_conditional_edges(
    #    "chatbot",
    #    tools_condition,
    #)

    # End tools
    end_tool_node = ToolNode(tools=end_tools)
    graph_builder.add_node("end_tools", end_tool_node)

    graph_builder.add_conditional_edges(
        "chatbot",
        route_tools,
        {"tools": "tools","end_tools":"end_tools", END: END},
    )

    ## Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")
    ## Any time an end tool is called, we end
    graph_builder.add_edge("end_tools", END)
    
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
    replies = []
    for event in graph.stream({"messages": prompt_input}):
        for value in event.values():
            reply = value["messages"][-1].content
            print("Assistant:", reply)
            replies.append(reply)
    return replies


# %% Functions called by other scripts
def summarize_website(url:str,sender:str)-> dict[str, str]:
    graph = get_graph_builder(sender).compile()
    replies = stream_graph_updates(url, graph)
    result = replies[-1]
    return result

