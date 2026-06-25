from groq import Groq

from backend.config.settings import settings


class AIReasoner:

    def __init__(self):

        self.client = Groq(
            api_key=settings.GROQ_API_KEY
        )

    def analyze_feature_completion(
        self,
        feature,
        commits
    ):

        commit_text = "\n".join(
            [
                commit["message"]
                for commit in commits
            ]
        )

        prompt = f"""
You are an AI software audit analyst.

Feature:
{feature}

Related GitHub commits:
{commit_text}

Analyze:
1. Is the feature likely completed?
2. Are commits semantically relevant?
3. Estimate implementation confidence.
4. Identify engineering risks.

Return concise analysis.
"""

        response = self.client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content