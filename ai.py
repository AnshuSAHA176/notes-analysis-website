#Here ai analyze the uploaded note

from groq import Groq
import re
import os
import json
import time
from dotenv import load_dotenv
loaded = load_dotenv()

API_KEY = os.environ.get('GROQ_API')

SUMMARY="""
You are an expert study assistant.

RULES:
- Summarize clearly
- Use bullet points
- Cover important concepts
"""
FLASK_PROMT="""

You are an expert study flashcard generator.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanations

FLASHCARD RULES:
- Generate EXACTLY 10 flashcards
- Cover important concepts
- Avoid duplicates

FORMAT:

[
  {
    "question":"What is DBMS?",
    "answer":"Database Management System"
  }
]
"""
QUIZ_PROMT="""
You are an expert MCQ quiz generator.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanations

QUIZ RULES:
- Generate EXACTLY 5 MCQs
- Cover important concepts
- Avoid duplicates

correct_answer MUST ONLY contain:
"A"
"B"
"C"
or
"D"

FORMAT:

[
  {
    "question":"What is DBMS?",
    "option_a":"Operating System",
    "option_b":"Database Management System",
    "option_c":"Compiler",
    "option_d":"Programming Language",
    "correct_answer":"B"
  }
]
"""
client = Groq(api_key=API_KEY)

def clean_texts(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('*', '')
    text = text.strip()
    return text
def create_chunk(text,size):
    chunks = []
    for i in range(0, len(text), size):

            chunk = text[i:i + size]

            chunks.append(chunk)
    print(f"Total Summary Chunks: {len(chunks)}")
    return chunks
    
def ask_ai(system_prompt, user_text, max_tokens):
    messages = [

            {
                "role": "system",
                "content": system_prompt
            },

            {
                "role": "user",
                "content": user_text
            }

        ]

    response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=messages,

            temperature=0.3,

            max_tokens=max_tokens

        )

    reply=response.choices[0].message.content
    return reply

def safe_json_loads(data):
    all_card=[]
    try:
        try:

                quiz = json.loads(data)

                all_card.extend(quiz)

                print("Quiz Chunk Done")

        except json.JSONDecodeError:

                print("Quiz JSON Error")

    

        return json.dumps(all_card)
    except Exception as e:
         return []
    

  
# =========================
# SUMMARY
# =========================

def Ai_summary(row_text):
    text=clean_texts(row_text)
    

    
    if len(text) < 15000:
        reply=ask_ai(SUMMARY,text,max_tokens=300)
        
        return reply
    
    else:

        chunks=create_chunk(text,size=4000)
        all_summaries = []

        for index, chunk in enumerate(chunks):

            print(f"Summary Chunk {index + 1}")

            reply=ask_ai(system_prompt=SUMMARY,user_text=chunk,max_tokens=300)
            all_summaries.append(reply)

            print("Summary Chunk Done")

            

        final_summary = "\n\n".join(all_summaries)

        return final_summary


# =========================
# FLASHCARD
# =========================

def Ai_FLASKCARD(row_text):
    text=clean_texts(text=row_text)

    chunks = create_chunk(text=text,size=3000)
    

    for index, chunk in enumerate(chunks):

        print(f"Flashcard Chunk {index + 1}")

        reply=ask_ai(FLASK_PROMT,user_text=chunk,max_tokens=1200)
    return safe_json_loads(reply)
        


# =========================
# QUIZ
# =========================

def Ai_Quiz(row_text):
    text=clean_texts(row_text)
    
    chunks=create_chunk(text,size=3000)

    print(f"Total Quiz Chunks: {len(chunks)}")

    

    for index, chunk in enumerate(chunks):

        print(f"Quiz Chunk {index + 1}")

        reply=ask_ai(QUIZ_PROMT,user_text=chunk,max_tokens=1200)

    return safe_json_loads(reply)
