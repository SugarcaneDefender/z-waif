import os
from dotenv import load_dotenv
load_dotenv()
BACKEND_TYPE = os.environ.get("TYPE")
match BACKEND_TYPE:
    case "oobabooga":
        from .oobabooga import *
    case "ollama":
        from .ollama import *
    case _:
        raise ValueError(f"Unknown backend type: {BACKEND_TYPE}")