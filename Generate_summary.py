from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

def split_transcript(transcript, words_per_chunk=2200):
    words = transcript.split()       # Break text into a list of words
    chunks = []                      # Create an empty list to hold our chunks
    
    # range(start, stop, step) 
    # Example: range(0, 10000, 2200) -> loops through 0, 2200, 4400, etc.
    for start in range(0, len(words), words_per_chunk):
        
        # Grab a slice of the list, e.g., words from index 0 to 2200
        slice_of_words = words[start : start + words_per_chunk]
        
        # Glue the words back together into a single text block with spaces
        text_block = " ".join(slice_of_words)
        
        # Add this new block to our chunks list
        chunks.append(text_block)
        
    return chunks

def generate(transcript):
    print("Generating meeting summary...")
    system_prompt = """
        You are an expert AI meeting assistant. Your job is to analyze meeting transcripts and extract key information.
        
        You MUST output your response in plain text format. 
        Do NOT include any conversational text before or after the summary.
        Do NOT invent or hallucinate information. If information is missing from the transcript, leave it blank or write "None".
    
        Format your response exactly like this, with each section on a new line:
        
        Title: A short, descriptive title for the meeting
        Date: The date of the meeting if mentioned
        Participants: List of names
        Key Points: Point 1, Point 2
        Action Items: Action 1 with assignee, Action 2 with assignee
        Decisions: Decision 1, Decision 2
        """
    
    llm = ChatGroq(
        model = "llama-3.1-8b-instant",
        api_key = api_key,
        temperature = 0.2,
        max_tokens = 500,
    )
    
    summaries = []
    transcript_chunks = split_transcript(transcript)

    for index, chunk in enumerate(transcript_chunks, start=1):
        print(f"Invoking the AI model for transcript part {index}/{len(transcript_chunks)}...")
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"This is transcript part {index} of {len(transcript_chunks)}. "
                "Extract only information explicitly present in this part.\n\n"
                f"{chunk}"
            ))
        ])
        response = llm.invoke(prompt.format_messages())
        summaries.append(response.content)

    # Join the summaries with a couple of newlines to separate chunks
    return "\n\n".join(summaries)
