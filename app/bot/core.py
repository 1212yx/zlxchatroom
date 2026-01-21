import openai
from app.models import AIModel
from flask import current_app

def get_bot_response(message, user_nickname, room_name):
    """
    Generator that yields chunks of response from AI.
    """
    # 1. Get Active AI Model
    model_config = AIModel.query.filter_by(is_enabled=True).order_by(AIModel.created_at.desc()).first()
    
    if not model_config:
        yield "Error: No active AI Model configured."
        return

    # 2. Prepare Context
    # We can add some system prompt or history here
    system_prompt = model_config.prompt or "You are a helpful assistant."
    # Add instruction to mention user
    system_prompt += f"\nUser's nickname is {user_nickname}. You are in room {room_name}."
    
    # 3. Call API
    try:
        client = openai.OpenAI(
            api_key=model_config.api_key,
            base_url=model_config.api_url
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        response = client.chat.completions.create(
            model=model_config.model_name,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=2048
        )

        # 4. Stream Response
        # Initial mention
        yield f"@{user_nickname} "
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        print(f"AI Error: {e}")
        yield f"Error calling AI: {str(e)}"
