import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def generate_questions(analysis: dict, subject: str = "General") -> dict:
    """
    Send parsed note analysis to LLM and get predicted exam questions.
    """
    if not client:
        return {"error": "OpenAI API key not configured", "questions": []}
    
    prompt = f"""You are an expert exam setter for {subject}.
    
Based on the following note analysis, generate exam questions:

DEFINITIONS: {analysis.get('definitions', [])}
COMPARISONS: {analysis.get('comparisons', [])}
LISTS/PROCESSES: {analysis.get('lists', [])}
FORMULAS: {analysis.get('formulas', [])}
TOP TOPICS: {[t['topic'] for t in analysis.get('top_topics', [])]}

Generate:
- 3 definition questions (2 marks each, Easy)
- 3 short answer questions (5 marks each, Medium)
- 2 long answer questions (10 marks each, Hard)
- 2 comparison questions (5 marks each, Medium)
- 2 numerical/application questions (5 marks each, Medium) if formulas exist

Format as JSON:
{{
  "questions": [
    {{
      "question": "...",
      "topic": "...",
      "type": "definition|short|long|comparison|numerical",
      "difficulty": "Easy|Medium|Hard",
      "marks": 2,
      "why_important": "..."
    }}
  ]
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        import json
        content = response.choices[0].message.content
        
        # Extract JSON from response
        if content and "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif content and "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        return json.loads(content.strip()) if content else {"questions": []}
        
    except Exception as e:
        return {"error": str(e), "questions": []}
