from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain.chat_models import ChatOpenAI
import openai
import constants  # Ensure this has your OpenAI API key
import dropbox
from io import BytesIO
import pytesseract
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

# Access environment variables
APIKEY = os.getenv("APIKEY")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
app = Flask(__name__)
os.environ["OPENAI_API_KEY"] = APIKEY
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Initialize model and vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(embedding_function=embeddings)
index = VectorStoreIndexWrapper(vectorstore=vectorstore)
chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-3.5-turbo"),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
)

# Cache to store responses
response_cache = {}

def extract_text_with_ocr(pdf_document):
    """Extract text using OCR for image-based PDFs."""
    text = ""
    try:
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            pix = page.get_pixmap()  # Render page to an image
            img = Image.open(io.BytesIO(pix.pil_tobytes("jpeg")))
            page_text = pytesseract.image_to_string(img)
            print(f"OCR extracted text from page {page_number}: {page_text[:100]}...")  # Log the first 100 characters
            text += page_text
    except Exception as e:
        print(f"Error during OCR extraction: {e}")
    return text

def extract_and_index_text_from_pdf_dropbox(file_path):
    """Extract text from a PDF stored in Dropbox and index it."""
    try:
        # Download the file from Dropbox into memory
        _, response = dbx.files_download(file_path)
        file_bytes = BytesIO(response.content)

        # Open the PDF file from bytes in memory
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""

        # Extract text from each page
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            page_text = page.get_text()
            print(f"Directly extracted text from page {page_number}: {page_text[:100]}...")  # Log the first 100 characters
            text += page_text

        # If direct text extraction fails, use OCR
        if not text.strip():
            print(f"No direct text found in PDF {file_path}, attempting OCR extraction.")
            text = extract_text_with_ocr(pdf_document)

        pdf_document.close()

        # Index the extracted text in the vector store
        if text.strip():
            vectorstore.add_texts([text])  # Add the extracted text to the vector store
            print(f"Text indexed successfully from {file_path}")
        else:
            print(f"Extracted text is empty for {file_path}")

        return text
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""

def store_text_in_dropbox(file_path, text):
    # Convert the text to bytes
    text_bytes = text.encode('utf-8')
    
    # Define a new path for the text file in Dropbox
    text_file_path = file_path.replace('.pdf', '.txt')

    try:
        # Upload the text file to Dropbox
        dbx.files_upload(text_bytes, text_file_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"Text successfully uploaded to {text_file_path}")
    except Exception as e:
        print(f"Error uploading text file to Dropbox: {e}")


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

        # Extract and index text from the uploaded PDF
        extracted_text = extract_and_index_text_from_pdf_dropbox(file_path)
        
        # Store the extracted text back into Dropbox as a .txt file
        if extracted_text.strip():
            store_text_in_dropbox(file_path, extracted_text)
        else:
            print("Extracted text is blank after processing.")

        link = dbx.sharing_create_shared_link_with_settings(file_path)
        return jsonify({'message': "File uploaded and processed successfully", 'link': link.url}), 200
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API error: {e}")
        return jsonify({'message': 'Failed to upload or process file on Dropbox', 'error': str(e)}), 500
    except Exception as e:
        print(f"General error during file upload: {e}")
        return jsonify({'message': 'An unexpected error occurred during file upload', 'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question')
    chat_history = data.get('chat_history', [])

    if not question:
        return jsonify({"message": "No question provided"}), 400

    try:
        # Make a request to the OpenAI Chat API with the new syntax
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Specify the model, e.g., gpt-4 or gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            max_tokens=150  # Adjust this based on your needs
        )
        
        # Extract the response content based on the new API structure
        answer = response.choices[0].message.content
        return jsonify({"answer": answer}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "An unexpected error occurred", "error": str(e)}), 500


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
