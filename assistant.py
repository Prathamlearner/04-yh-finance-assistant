from openai import OpenAI

from openai.types.beta.threads.run import Run
from openai.types.beta.thread import Thread
from openai.types.beta.assistant import Assistant

avaliable_tools = [
    {"type": "code_interpreter"},
    {
        "type": "function",
        "function":  {
            "name": "get_stock_price",
            "description": "Get the current stock price",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock symbol"
                    }
                },
                "required": [
                    "symbol"
                ]
            }
        }
    },
    {
        "type": "function",
        "function":  {
            "name": "get_stock_data",
            "description": "Fetches historical stock data for the given ticker symbol and time period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol."
                    },
                    "period": {
                        "type": "string",
                        "description": "The time period for which historical data is requested (e.g., '1m' for 1 month)."
                    }
                },
                "required": [
                    "ticker",
                    "period"
                ]
            }
        }
    }

]


class StockAssistant:
    def __init__(self, model: str = "gpt-3.5-turbo-1106"):
        self.client = OpenAI()
        self.model = model
        self.assistant: Assistant | None = None
        self.thread: Thread | None = None
        self.run: Run | None = None

    # Update API KEY and Get the client object
    def init_client(self, api_key: str) -> OpenAI:
        self.client.api_key = api_key
        return self.client

    def list_assistants(self) -> list:
        """Retrieve a list of assistants."""
        assistants_list = self.client.beta.assistants.list()
        assistants = assistants_list.model_dump()
        return assistants['data'] if 'data' in assistants else []

    def modifyAssistant(self, assistant_id: str, new_instructions: str, tools: list, file_obj: list[str]) -> Assistant:
        """Update an existing assistant."""
        print("Updating edisting assistant...")
        self.assistant = self.client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=new_instructions,
            tools=tools,
            model=self.model,
            file_ids=file_obj
        )
        return self.assistant

    def find_and_set_assistant_by_name(self, name: str, instructions: str, tools: list, file_obj: list[str]) -> None:
        """Find an assistant by name and set it if found."""
        assistants = self.list_assistants()
        print("Retrieved assistants list...")
        if self.assistant is None:  # Check if assistant is not already set
            for assistant in assistants:
                if assistant['name'] == name:
                    print("Found assistant...",  assistant['name'] == name)
                    print("Existing Assitant ID", assistant['id'])
                    # self.assistant = assistant
                    self.modifyAssistant(
                        assistant_id=assistant['id'],
                        new_instructions=instructions,
                        tools=tools,
                        file_obj=file_obj
                    )
                    break

    def create_assistant(self, name: str, instructions: str, tools: list, file_obj: list[str], model: str = "gpt-3.5-turbo-1106") -> Assistant:
        """Create or find an assistant."""
        self.find_and_set_assistant_by_name(
            name=name,
            instructions=instructions,
            tools=tools,
            file_obj=file_obj)
        if self.assistant is None:  # Check if assistant is not already set
            print("Creating new assistant...")
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools,
                model=model,
                file_ids=file_obj
            )
        return self.assistant  # Return the assistant object
