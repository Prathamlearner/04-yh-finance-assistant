from openai import OpenAI

from openai.types.beta.threads.run import Run
from openai.types.beta.thread import Thread
from openai.types.beta.assistant import Assistant
from typing import Literal

avaliable_tools = [{
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
}]


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

    def list_files(self, purpose: str = 'assistants') -> list:
        """Retrieve a list of files with the specified purpose."""
        files = self.client.files.list(purpose=purpose)
        file_list = files.model_dump()
        return file_list['data'] if 'data' in file_list else []

    def find_file_id_by_name(self, filename: str, purpose: str = 'assistants') -> str | None:
        """Check if the file exists in the OpenAI account and return its ID."""
        files = self.list_files(purpose=purpose)
        for file in files:
            print("Is this a Duplicate File?", file['filename'] == filename)
            if file['filename'] == filename:
                print("file['id']", file['id'])
                return file['id']
        return None

    def create_file(self, file_path: str, purpose: Literal['fine-tune', 'assistants'] = 'assistants') -> str:
        """Create or find a file in OpenAI. 
        https://platform.openai.com/docs/api-reference/files/list
        If file is already uploaded with same name then 
        we will use it rather than creating a new one. """

        existing_file_id = self.find_file_id_by_name(file_path, purpose)

        print("found existing file...", existing_file_id)

        if existing_file_id:
            self.file_id = existing_file_id
            return existing_file_id
        else:
            with open(file_path, "rb") as file:
                file_obj = self.client.files.create(file=file, purpose=purpose)
                self.file_id = file_obj.id
                return file_obj.id

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
