from flask import Flask, request, jsonify
import os
import fitz  # PyMuPDF
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
import openai
import constants  # Make sure this has your OpenAI API key

app = Flask(__name__)
os.environ["OPENAI_API_KEY"] = constants.APIKEY

# Initialize model
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(embedding_function=embeddings)
index = VectorStoreIndexWrapper(vectorstore=vectorstore)
chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-3.5-turbo"),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
)

def extract_text_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    text = ""
    for page in pdf_document:
        text += page.get_text()
    pdf_document.close()
    return text

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        text = extract_text_from_pdf(filepath)
        # Update index with new document
        document = {"text": text, "source": file.filename}
        index.add_document(document)
        return jsonify({"message": "File uploaded and indexed successfully"}), 200
    return jsonify({"message": "Invalid file format"}), 400

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"message": "No question provided"}), 400

    chat_history = data.get('chat_history', [])
    result = chain({"question": question, "chat_history": chat_history})
    return jsonify({"answer": result['answer']}), 200

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
