import tiktoken

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count the number of tokens in a given text using tiktoken for the specified model."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def truncate_to_budget(text: str, max_tokens: int = 1500, model: str = "gpt-3.5-turbo") -> str:
    """Truncate the text so that its token count does not exceed max_tokens.
    Simple greedy truncation from the end.
    """
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    truncated = encoding.decode(tokens[:max_tokens])
    return truncated
