from openai import OpenAI
from main import get_settings

# singleton
class Openai:

    client = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls.client = OpenAI(api_key=get_settings().openai_api_key)
            cls._instance = super(Openai, cls).__new__(cls)
        return cls._instance

    async def retry_generate_schema(self, system_prompt='', user_prompt='', json_schema={}):
        count = 0
        final_result = {}
        while count <= 3 and True:
            count += 1
            result = await self.generate_structure_outputs(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema=json_schema,
            )
            final_result = result
            if final_result.get('is_resolved') == True:
                break
        return final_result

    async def generate_structure_outputs(self, system_prompt='', user_prompt='', json_schema={}):
        try:
            response = Openai.client.responses.parse(
                model=get_settings().model_structure_outputs,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text_format=json_schema,
                temperature=0
            )

            event = response.output_parsed
            return {'is_resolved': True, 'data': event}
        except Exception as e:
            print(e)
            return {'is_resolved': False}

