from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
import openai
import constants  # Ensure this has your OpenAI API key
import dropbox

app = Flask(__name__)
os.environ["OPENAI_API_KEY"] = constants.APIKEY
dbx = dropbox.Dropbox(constants.DROPBOX_ACCESS_TOKEN)

# Initialize model
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(embedding_function=embeddings)
index = VectorStoreIndexWrapper(vectorstore=vectorstore)
chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-3.5-turbo"),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
)

# Cache to store responses
response_cache = {}

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

    filename = secure_filename(file.filename)
    try:
        # Save the file directly to Dropbox
        file_path = f'/uploads/{filename}'  # Path in Dropbox
        dbx.files_upload(file.read(), file_path, mode=dropbox.files.WriteMode("overwrite"))
        link = dbx.sharing_create_shared_link_with_settings(file_path)
        return jsonify({'message': "File uploaded successfully", 'link': link.url}), 200
    except dropbox.exceptions.ApiError as e:
        return jsonify({'message': 'Failed to upload to Dropbox', 'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question')
    chat_history = data.get('chat_history', [])

    if not question:
        return jsonify({"message": "No question provided"}), 400

    cache_key = question + "".join(chat_history)  # Simple cache key
    if cache_key in response_cache:
        return jsonify({"answer": response_cache[cache_key]}), 200

    try:
        # Updated to use the new invoke method
        result = chain.invoke({"question": question, "chat_history": chat_history})
        response_cache[cache_key] = result['answer']  # Store response in cache
        return jsonify({"answer": result['answer']}), 200
    except Exception as e:
        error_message = str(e)
        if "insufficient_quota" in error_message:
            return jsonify({"message": "API quota exceeded, please try again later."}), 429
        return jsonify({"message": "Error processing the request."}), 500


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
