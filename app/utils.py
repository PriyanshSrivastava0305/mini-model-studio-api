# app/utils.py
from typing import List, Dict

def messages_for_openai(system_prompt: str, prior_messages: List[Dict]) -> List[Dict]:
    """
    Build messages array for OpenAI: prepend system prompt, then prior messages.
    prior_messages is a list of {role, content}
    """
    msgs = [{"role": "system", "content": system_prompt}]
    msgs.extend(prior_messages)
    return msgs
