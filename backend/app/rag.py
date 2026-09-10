from pathlib import Path

from app.config import settings

def load_documents() -> list[dict]:
    knowledge_base_path= Path(settings.knowledge_base_path)
    documents =[]
    
    for file_path in knowledge_base_path.glob("*.md"):
        content= file_path.read_text(encoding="utf-8")
        
        documents.append(
            {
            "source_name": file_path.name,
            "source_type":"policy",
            "content":content,
            "access_level":"general",
            }
            
        )
        
    return documents


def chunk_text(text:str,chunk_size:int=700,overlap: int =100)-> list[str]:
    chunks=[]
    start=0
    
    while start < len(text):
        end=start + chunk_size
        chunk = text[start:end].strip()
        
        if chunk:
            chunks.append(chunk)
        start= end- overlap
        
    return chunks
