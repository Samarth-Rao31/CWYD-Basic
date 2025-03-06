import os
import streamlit as st
from CWYD.ocr_text import process_pdf, process_image, translateText, detect_lang
from langchain_openai import AzureOpenAIEmbeddings
from langchain_openai.chat_models.azure import AzureChatOpenAI
# from langchain.vectorstores.chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
# from langchain.document_loaders.unstructured import UnstructuredFileLoader
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import string
import random

load_dotenv()

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')



st.header("Chat With Your Data", divider='rainbow')
st.subheader('File types supported: PDF/DOCX/TEXT/JPG/PNG/JPEG')

llm = AzureChatOpenAI(model="gpt-35-turbo-16k",
                      deployment_name="yokogawaconnectgpt16k",
                      azure_endpoint="https://openai-yokogawa-internal.openai.azure.com/",
                      openai_api_type="azure",
                      api_key=os.getenv("OPENAI_API_KEY"),
                      api_version="2023-07-01-preview",
                      temperature=0.7,
                      streaming=True)

embeddings = AzureOpenAIEmbeddings(
        deployment="yokogawaconnectsharepoint",
        model="text-embedding-ada-002",
        azure_endpoint="https://openai-yokogawa-internal.openai.azure.com/",
        openai_api_type="azure",
        api_key=os.getenv("OPENAI_API_KEY"),
        api_version="2023-07-01-preview"
    )

def generate_session_id(length=8):
    """To generate Random sessionID"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

with st.sidebar:
    uploaded_files = st.file_uploader("Please upload your files", accept_multiple_files=True, type=["pdf", "docx", "txt", ".png", ".jpg", ".jpeg"])
    st.info("Please refresh the browser if you decide to upload more files to reset the session", icon="🚨")
    st.info("Please refer to the FAQ of Y-ChatGPT to check how to structure the prompt for better responses.", icon="❗")

if uploaded_files:
    st.write(f"Number of files uploaded: {len(uploaded_files)}")

    if "processed_data" not in st.session_state:
        documents = []
        document_chunks = []
        documents_e = []
        

        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(os.getcwd(), uploaded_file.name)

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                try:
                    if file_path.endswith((".pdf",".PDF")):
                        text = process_pdf(file_path)
                        documents_e.append(text)

                    if file_path.endswith((".docx", ".txt",".DOCX",".TXT")):
                        loader = UnstructuredFileLoader(file_path)
                        loaded_documents = loader.load()
                        documents.extend(loaded_documents)


                    if file_path.endswith((".jpg", ".png", ".jpeg",".JPG",".PNG",".JPEG")):
                        text = process_image(file_path)
                        documents_e.append(text)
                        print(documents_e)

                except Exception as e:
                    st.error(f"Please check the file  {file_path}")
                finally:
                    try:
                        os.remove(file_path)

                    except Exception as e:
                        continue
                
        
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        
        for doc in documents if file_path.endswith((".docx", ".txt",".DOCX",".TXT")) else documents_e:
            document_c = text_splitter.split_text(doc.page_content if file_path.endswith((".docx", ".txt",".DOCX",".TXT")) else doc)
            for document in document_c:
                document_chunks.append(document)

        vectorstore = Chroma.from_texts(document_chunks, embeddings, collection_name=generate_session_id(8))

        
        st.session_state.processed_data = {
            "document_chunks": document_chunks,
            "vectorstore": vectorstore,
        }

    else:
        document_chunks = st.session_state.processed_data["document_chunks"]
        vectorstore = st.session_state.processed_data["vectorstore"]

    qa = ConversationalRetrievalChain.from_llm(llm, vectorstore.as_retriever())

    

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask your questions?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        result = qa({"question": prompt, "chat_history": [(message["role"], message["content"]) for message in st.session_state.messages]})
        to = detect_lang(prompt)
        if detect_lang(result['answer']) != detect_lang(prompt):
            result['answer'] = translateText(result['answer'],to)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            full_response = result["answer"]
            message_placeholder.markdown(full_response + "|")
        message_placeholder.markdown(full_response)    
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        

else:
    st.write("Please upload your files:")