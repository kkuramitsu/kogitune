###
# OpenAI
import json

from .commons import *
from .models import Model

class OpenAIModel(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_path = adhoc.get(kwargs, "_subpath|model_path|model")
        openai = adhoc.safe_import('openai')
        api_key = adhoc.get(kwargs, "api_key|OPENAI_API_KEY|!!")
        try:
            self.client = openai.OpenAI(api_key=api_key)
        except BaseException as e:
            adhoc.print('環境変数 OPENAI_API_KEY を設定してね', repr(e))
            adhoc.exit(throw=e)

    def supported_gen_args(self) -> List[str]:
        return [
            ## https://platform.openai.com/docs/api-reference/chat/create
            "_max_tokens|max_tokens|max_new_tokens|=256",
            "_n|n|num_return_sequences",
            "temperature",
            "top_p",
            "frequency_penalty",
            # "logit_bias",
            # "logprobs",
            # "top_logprobs",
            # "presence_penalty",
            # "response_format",
            # "seed",
            # "service_tier",
            "stop",
            # "stream",
        ]
    
    def unwrap(self):
        return self.client

    def generate_s(self, input_text: str, /, **gen_args):
        gen_args = self.filter_gen_args(**gen_args)
        if isinstance(input_text, str):
            input_text = self.get_default_messages(input_text)
        response = self.client.chat.completions.create(
            model=self.model_path,
            messages=input_text,
            **gen_args,
        )
        responses = [choice.message.content for choice in response.choices]
        return singlefy_if_single(responses)

OpenAIModel.regiser("openai")


class BedrockModel(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_path = adhoc.get(kwargs, "_subpath|model_path|model")
        boto3 = adhoc.safe_import('boto3')
        self.client = boto3.client(
            service_name='bedrock-runtime', 
            region_name=adhoc.get(kwargs, 'region_name|=us-west-2')
        )

    def supported_gen_args(self) -> List[str]:
        return [
            "_max_tokens|max_tokens|max_new_tokens|=256",
            "_n|n|num_return_sequences",
            "temperature",
            "top_p",
        ]

    def generate_s(self, input_text: Union[List, str], /, **kwargs):
        gen_args = self.filter_gen_args(kwargs)

        if isinstance(input_text, str):
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "prompt": input_text,
                    **gen_args,
                }),
                contentType='application/json'
            )
            # レスポンスの読み取り
            response_body = response['body'].read().decode('utf-8')
            response_json = json.loads(response_body)
            generated_text = response_json.get('completion', '')
            return generated_text
        else:
            response = self.client.invoke_model(
                modelId=self.model_path, 
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": input_text
                    **gen_args
                }), 
                accept='application/json', 
                contentType='application/json'
            )
            response_body = json.loads(response.get('body').read())
            output_text = response_body["content"][0]["text"]
            return output_text

BedrockModel.regiser("anthropic")

# class BedrockModel(Model):
#     def __init__(self, model_path, kwargs):
#         super().__init__(model_path, kwargs)
#         try:
#             import boto3

#             self.bedrock = boto3.client(
#                 "bedrock-runtime",
#                 aws_access_key_id=adhoc.get(kwargs, "aws_access_key_id"],
#                 aws_secret_access_key=adhoc.get(kwargs, "aws_secret_access_key"],
#                 region_name=adhoc.get(kwargs, "region_name|=ap-northeast-1"],
#             )
#         except ModuleNotFoundError as e:
#             raise e
#         default_args = {
#             "max_tokens_to_sample": adhoc.get(kwargs, "max_tokens|max_length|=512"],
#             "temperature": adhoc.get(kwargs, "temperature|=0.2"],
#             "top_p": adhoc.get(kwargs, "top_p|=0.95"],
#         }
#         self.generate_args = default_args

#     def check_and_append_claude_format(self, prompt: str) -> str:
#         ## FIXME: 改行の位置はここでいいのか？
#         human_str = "\n\nHuman:"
#         assistant_str = "\n\nAssistant:"

#         if human_str not in prompt:
#             prompt = human_str + prompt

#         if assistant_str not in prompt:
#             prompt += assistant_str

#         return prompt

#     def generate_text(self, prompt: str) -> str:
#         prompt = self.check_and_append_claude_format(prompt)
#         body = json.dumps(
#             {
#                 "prompt": prompt,
#                 "anthropic_version": "bedrock-2023-05-31",
#                 **self.generate_args,
#             }
#         )
#         response = self.bedrock.invoke_model(body=body, modelId=self.model_path)
#         response_body = json.loads(response.get("body").read())
#         return response_body.get("completion")
