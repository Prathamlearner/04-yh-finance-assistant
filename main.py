from openai import OpenAI
import streamlit as st

import yfinance as yf
import time
import os
import json
import time
import logging

from dotenv import load_dotenv, find_dotenv

from openai.types.beta.threads.run import Run, RequiredActionSubmitToolOutputs
from openai.types.beta.thread import Thread
from openai.types.beta.thread_create_and_run_params import ThreadMessage
from typing import Union

_: bool = load_dotenv(find_dotenv())  # read local .env file

# connect with openai server
client: OpenAI = OpenAI()

assistant_id = os.environ.get("ASSISTANT_ID")

if not assistant_id:
    st.sidebar.error(f"Assistant is Sleeping - come back later!")
    st.stop()


def getStockPrice(ticker: dict[str, str]) -> dict[str, Union[float, str]]:
    """
    Fetches the latest closing stock price for the given ticker symbol.

    Parameters:
    ticker (str): The stock ticker symbol.

    Returns:
    dict: A dictionary containing either the price or an error message.
    """
    try:
        # Fetch data for the given ticker symbol
        stock = yf.Ticker(ticker)

        # Get the latest closing price
        hist = stock.history(period="1d")
        latest_price = hist['Close'].iloc[-1]
        return {"price": latest_price}
    except Exception as e:
        # Log the specific error
        return {"error": f"Error fetching price for {ticker}"}


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

        logging.info(f"Tool Call ID: {tool_call_id}, Function Name: {
                     function_name}, Function Arguments: {function_args}")

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
                logging.error(f"Invalid JSON input for tool call ID {
                              tool_call_id}: {function_args}")
                st.sidebar.error(f"Invalid input for {symbol}")

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

# Set up the Streamlit page title & icon
st.set_page_config(
    page_title="Company Investment AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.header(" :dollar: Stock & Company Clients AI")

# Get User Open AI API Key
openai_api_key = st.sidebar.text_input(
    "Your OpenAI API Key:", placeholder="sk-aAdsadklnvsd", value=os.getenv("OPENAI_API_KEY"))

if openai_api_key:
    client.api_key = openai_api_key

# Button to start chat
if st.sidebar.button("Start Chat"):

    if not openai_api_key:
        st.sidebar.error("Please enter your OpenAI API Key")
        st.stop()

    st.session_state.start_chat = True

    thread: Thread = client.beta.threads.create()
    # Step 02: Initialze the thread
    st.session_state.thread_id = thread.id
    st.session_state.start_chat = True
    st.write("Chat started!", thread.id)

# utility to process citations in assistant text output


def process_citations(text):
    process_text = text.content[0].text.value
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
    if prompt := st.chat_input("Get tesla latest stock price!... Which companies we work with?"):

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
            logging.error(f"Error adding message to thread")
            st.sidebar.error(
                "Error in processing your request. Please refresh and try again later.")
            st.stop()  # Optionally stop further execution

        # Step =4: Create a Run

        run: Run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
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
                    logging.info("No action is required for this run.")

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
