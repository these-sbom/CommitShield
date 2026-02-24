import os
import json
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from mistralai import Mistral
from typing import List, Dict

load_dotenv()

class LLM(ABC):
    @property
    @abstractmethod
    def base_url(self):
        pass
    
    @property
    @abstractmethod
    def model_name(self):
        pass

    @property
    def output_max_tokens(self):
        return 1024

    @abstractmethod
    def get_chat_answer(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> str:
        pass

    @abstractmethod
    def get_chat_answer_in_json_format(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> Dict[str, str]:
        # Ensure that the returned value ('value') complies with the following JSON format :
        # { 'answer' : value } 
        pass

class RemoteLLM(LLM):
    @property
    @abstractmethod
    def api_key(self):
        pass

    @abstractmethod
    def get_client(self):
        pass
    
    @abstractmethod
    def get_chat_answer(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> str:
        pass

    @abstractmethod
    def get_chat_answer_in_json_format(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> Dict[str, str]:
        pass

class LocalLLM(LLM):
    @property
    def base_url(self):
        return os.environ['LOCALHOST_URL']

    def get_answer(self, response: Dict) -> str:
        return response.json()['message']['content']

    def get_chat_answer(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> str:
        response = requests.post(
            f'{self.base_url}/api/chat',
            json={
                'model': self.model_name,
                'messages': messages,
                'stream': stream,
                'options': {
                    'num_predict': self.output_max_tokens,
                    'temperature': temperature
                }
            }
        )
        return self.get_answer(response)

    def get_chat_answer_in_json_format(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> Dict[str, str]:
        response = requests.post(
            f'{self.base_url}/api/chat',
            json={
                'model': self.model_name,
                'messages': messages,
                'stream': stream,
                'format': 'json',
                'options': {
                    'num_predict': self.output_max_tokens,
                    'temperature': temperature
                }
            }
        )
        return {
            'answer': self.get_answer(response)
        }

class DeepseekCoder6Dot7BLLM(LocalLLM):
    @property
    def model_name(self):
        return 'deepseek-coder:6.7b'

class DeepseekCoderV216BLLM(LocalLLM):
    @property
    def model_name(self):
        return 'deepseek-coder-v2:16b'

class DeepseekCoderV2236BLLM(LocalLLM):
    @property
    def model_name(self):
        return 'deepseek-coder-v2:236b'

class Devstral2512LLM(RemoteLLM):
    LIMIT_NUMBER_OF_TOKENS_PER_MINUTE = 500000
    NUMBER_OF_SECONDS_IN_ONE_MINUTE = 60
    LIMIT_NUMBER_OF_INPUT_TOKENS = 100000
    __number_of_tokens_since_minute_beginning = 0
    __start_date_of_the_minute_in_seconds = datetime.now(timezone.utc)

    @property
    def base_url(self):
        pass

    @property
    def api_key(self):
        return os.environ['MISTRAL_API_KEY']

    @property
    def model_name(self):
        return 'devstral-2512'

    def get_client(self):
        return Mistral(api_key=self.api_key)
    
    def get_answer(self, response):
        return response.json()['message']['content']

    def check_rate_limit(self):
        maximum_future_number_of_tokens = self.__number_of_tokens_since_minute_beginning + self.LIMIT_NUMBER_OF_INPUT_TOKENS + self.output_max_tokens

        if maximum_future_number_of_tokens > self.LIMIT_NUMBER_OF_TOKENS_PER_MINUTE:
            now = datetime.now(timezone.utc)
            time_since_minute_beginning = now - self.__start_date_of_the_minute_in_seconds
            time_to_wait_before_next_minute = self.NUMBER_OF_SECONDS_IN_ONE_MINUTE - time_since_minute_beginning.seconds
            print('Wait (Mistral AI API rate limit) :', time_to_wait_before_next_minute.seconds)
            time.sleep(time_to_wait_before_next_minute.seconds)

    def update_number_of_tokens(self, response):
        request_number_of_tokens = response.usage.total_tokens
        self.__number_of_tokens_since_minute_beginning += request_number_of_tokens

    def update_rate_limit_information(self):
        now = datetime.now(timezone.utc)
        time_since_minute_beginning = now - self.__start_date_of_the_minute_in_seconds

        if time_since_minute_beginning.seconds >= self.NUMBER_OF_SECONDS_IN_ONE_MINUTE:
            self.__start_date_of_the_minute_in_seconds = datetime.now(timezone.utc)
            self.__number_of_tokens_since_minute_beginning = 0

    def get_response(self, messages: List[Dict[str, str]], temperature: float, stream: bool, response_format: Dict[str, str]) -> Dict:
        self.update_rate_limit_information()
        self.check_rate_limit()
        response = self.get_client().chat.complete(
            model=self.model_name,
            messages=messages,
            max_tokens=self.output_max_tokens,
            temperature=temperature,
            stream=stream,
            response_format=response_format
        )
        self.update_number_of_tokens(response)
        return response

    def get_chat_answer(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> str:
        return self.get_response(
            messages,
            temperature,
            stream,
            {
                "type": "text"
            }
        )

    def get_chat_answer_in_json_format(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> Dict[str, str]:
        response = self.get_response(
            messages,
            temperature,
            stream,
            {
                'type': 'json_object'
            }
        )
        json_response = json.loads(response.choices[0].message.content)
        return json_response

class OpenAILLM(RemoteLLM):
    def get_client(self):
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
    
    def get_chat_answer(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> str:
        response = self.get_client().chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=self.output_max_tokens,
            temperature=temperature,
            stream=stream
        )
        return response.choices[0].message.content
    
    def get_chat_answer_in_json_format(self, messages: List[Dict[str, str]], temperature: float, stream: bool) -> Dict[str, str]:
        response = self.get_client().chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=self.output_max_tokens,
            temperature=temperature,
            stream=stream,
            response_format={
                'type': 'json_object'
            }
        )
        json_response = json.loads(response.choices[0].message.content)
        return json_response

class DeepseekCoderOpenAILLM(OpenAILLM):
    @property
    def base_url(self):
        return 'https://api.deepseek.com'
    
    @property
    def api_key(self):
        return os.environ['OPENAI_API_KEY']
    
    @property
    def model_name(self):
        return 'deepseek-coder'
