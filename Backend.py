from flask import Flask, request, jsonify, render_template
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

@app.route('/')
def index():
    return render_template('Frontend.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    # Save the file to a location
    file.save(f"./uploads/{file.filename}")
    
    # Return a success message or further processing
    return jsonify({'message': f"File {file.filename} uploaded successfully"}), 200

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question')
    chat_history = data.get('chat_history', [])
    
    if not question:
        return jsonify({"message": "No question provided"}), 400

    try:
        result = chain({"question": question, "chat_history": chat_history})
        return jsonify({"answer": result['answer']}), 200
    except openai.error.RateLimitError as e:
        app.logger.warning(f"Rate limit error: {str(e)}")
        return jsonify({"message": "Rate limit exceeded, please try again later."}), 429
    except Exception as e:
        app.logger.error(f"Error in /query route: {str(e)}")
        return jsonify({"message": "Error processing the request."}), 500



if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
