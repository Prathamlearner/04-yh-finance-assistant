import streamlit as st

import time
import os
import json
import time
# import logging

from dotenv import load_dotenv, find_dotenv

from openai.types.beta.threads.run import Run, RequiredActionSubmitToolOutputs
from openai.types.beta.thread import Thread
from openai.types.beta.assistant import Assistant

from assistant import avaliable_tools, StockAssistant
from functions import getStockPrice, getStockData
from seed import STOCK_ASSISTANT_SEEED_PROMPT

import pandas as pd


_: bool = load_dotenv(find_dotenv())  # read local .env file


def handle_assistant_function_call(submit_tool_outputs: RequiredActionSubmitToolOutputs) -> None:
    """
    Handles function calls required by an assistant.

    Parameters:
    submit_tool_outputs (RequiredActionSubmitToolOutputs): Object containing details about the tool calls.
    """

    tools_to_call = submit_tool_outputs.tool_calls
    tools_output_array: list = []

    for each_tool in tools_to_call:
        tool_call_id = each_tool.id
        function_name = each_tool.function.name
        function_args = each_tool.function.arguments

        # logging.info(f"Tool Call ID: {tool_call_id}, Function Name: {
        #              function_name}, Function Arguments: {function_args}")

        if function_name == "get_stock_price":
            try:
                arguments_dict = json.loads(function_args)
                symbol = arguments_dict["symbol"]
                st.sidebar.write('Get stock price for', symbol)

                output = getStockPrice(symbol)

                if "price" in output:
                    tools_output_array.append({
                        "tool_call_id": tool_call_id,
                        "output": f"Price: {output['price']}"
                    })
                    st.sidebar.write(f"Price: {output['price']}")
                else:
                    tools_output_array.append({
                        "tool_call_id": tool_call_id,
                        "output": output["error"]
                    })
                    st.sidebar.error(output["error"])
            except json.JSONDecodeError:
                # logging.error(f"Invalid JSON input for tool call ID {
                #               tool_call_id}: {function_args}")
                st.sidebar.error(f"Invalid input for {symbol}")

        elif function_name == "get_stock_data":
            try:
                arguments_dict = json.loads(function_args)
                ticker = arguments_dict["ticker"]
                period = arguments_dict["period"]
                st.sidebar.write(ticker, 'Historical Stocks Data For', period)

                output = getStockData(ticker, period)

                if "history_data" in output:
                    history_data = output["history_data"]

                    # Check if history_data is a DataFrame
                    if isinstance(history_data, pd.DataFrame):
                        # Convert DataFrame to string representation
                        history_data_str = history_data.to_string(index=False)
                        tools_output_array.append({
                            "tool_call_id": tool_call_id,
                            "output": history_data_str
                        })
                        st.sidebar.write(history_data)
                    else:
                        # Handle the case where history_data is not a DataFrame
                        tools_output_array.append({
                            "tool_call_id": tool_call_id,
                            "output": str(history_data)
                        })
                        # Optionally, you can provide additional handling for non-DataFrame types
                        st.sidebar.error(f"Unexpected 'history_data': {
                                         type(history_data)}")

                else:
                    tools_output_array.append({
                        "tool_call_id": tool_call_id,
                        "output": output["error"]
                    })
                    st.sidebar.error(output["error"])
            except json.JSONDecodeError:
                st.sidebar.error(f"Invalid input for {ticker}")

    print("Submitting tool outputs...")
    print("run_id", run.id)
    print("thread_id", st.session_state.thread_id)

    print("tools_output_array", tools_output_array)
    # submit response to assistant
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=st.session_state.thread_id,
        run_id=run.id,
        tool_outputs=tools_output_array
    )


# Session State Variables
if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = []

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None


# Set up the Streamlit page title & icon
st.set_page_config(
    page_title="Company Investment AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.header(" :dollar: Stock Data AI")

# Get User Open AI API Key

st.sidebar.header("Fetch Fresh & Historical Stock Data")

openai_api_key = st.sidebar.text_input(
    "Enter Your OpenAI API Key:", placeholder="sk-aAdsadklnvsd", value=os.getenv("OPENAI_API_KEY"))

stock_assistant_instace: StockAssistant = StockAssistant()

if openai_api_key:
    client = stock_assistant_instace.init_client(openai_api_key)


# Button to start chat
if st.sidebar.button("Start Chat"):

    if not openai_api_key:
        st.sidebar.error("Please enter your OpenAI API Key")
        st.stop()

    # Assert to satisfy Mypy's type checking - we have already added the check above but mypy doesn't know that!!!
    # This assertion will inform Mypy that beyond this point in the code, assistant_id cannot be None. Here's how you can do it:
    assert openai_api_key is not None, "Open AI API Key must be set"

    # Step 01: Create an Assistant If not Present

    stock_assistant: Assistant = stock_assistant_instace.create_assistant(
        name="Stocks, Charts And Investment AI",
        instructions=STOCK_ASSISTANT_SEEED_PROMPT,
        tools=avaliable_tools,
        file_obj=[]
    )

    assistant_id = stock_assistant.id
    st.session_state.assistant_id = assistant_id

    st.session_state.start_chat = True

    thread: Thread = client.beta.threads.create()
    # Step 02: Initialze the thread
    st.session_state.thread_id = thread.id
    st.session_state.start_chat = True
    st.write("Chat started!", thread.id)

# utility to process citations in assistant text output


def process_citations(text):
    process_text = text.content[0].text.value
    print('====================', process_text)
    return process_text


# show chat interface when chat session is started
if st.session_state.start_chat:

    if "message" not in st.session_state:
        st.session_state.message = []

    # show existing messages in chat
    for message in st.session_state.message:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # chat input
    if prompt := st.chat_input("Get tesla latest stock price!... share meta last month historical stock data?"):

        # adding user in state
        st.session_state.message.append({
            "role": "user",
            "content": prompt
        })

        # Show the user prompt
        with st.chat_message("user"):
            st.write(prompt)

        try:
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                content=prompt,
                role="user"
            )
        except Exception:
            # logging.error("Error adding message to thread")
            st.sidebar.error(
                "Error in processing your request. Please refresh and try again later.")
            st.stop()  # Optionally stop further execution

        # Step =4: Create a Run

        run: Run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=st.session_state.assistant_id,
            instructions="This is the Company Member, Investment AI Whiz. Answer respectufully and accurately.",
        )

        # Step 05: polling the thread to coplete and retrive assistant response
        while run.status not in ["completed", "failed"]:
            st.sidebar.write(run.status)
            time.sleep(3)
            # manage assistant function calling
            if run.status == "requires_action":
                # Check if required_action is not None before calling the function
                if run.required_action is not None:
                    handle_assistant_function_call(
                        run.required_action.submit_tool_outputs)
                else:
                    # Handle the case where no action is required
                    # This could be logging, displaying a message, etc.
                    print("No action is required for this run.")
            print("Polling for run completion...")
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )

        st.sidebar.write(run.status)

        # Step 06: Retrive and Display the assistant response

        assistant_run_response = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        assistant_message_in_run = [
            message for message in assistant_run_response
            if message.run_id == run.id and message.role == "assistant"
        ]

        for message in assistant_message_in_run:
            processes_response = process_citations(message)
            st.session_state.message.append({
                "role": "assistant",
                "content": processes_response
            })
            with st.chat_message("assistant"):
                st.markdown(processes_response, unsafe_allow_html=True)
