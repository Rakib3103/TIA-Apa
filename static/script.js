const chatInput = document.querySelector("#chat-input");
const sendButton = document.querySelector("#send-btn");
const chatContainer = document.querySelector(".chat-container");
const deleteButton = document.querySelector("#delete-btn");
const uploadButton = document.querySelector("#upload-btn");
const uploadInput = document.querySelector("#upload-input"); // Corrected ID reference

const loadDataFromLocalStorage = () => {
    const savedChats = localStorage.getItem("all-chats");

    if (savedChats) {
        chatContainer.innerHTML = savedChats;
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    } else {
        showDefaultText();
    }
};

const showDefaultText = () => {
    const defaultText = `<div class="default-text">
                            <h1>টিয়া আপা</h1>
                            <p>আপাকে জিজ্ঞেস করুন।<br> আপনার চ্যাট এখানে প্রদর্শিত হবে।</p>
                        </div>`;
    chatContainer.innerHTML = defaultText;
};

const createChatElement = (content, className) => {
    const chatDiv = document.createElement("div");
    chatDiv.classList.add("chat", className);
    chatDiv.innerHTML = content;
    return chatDiv;
};

const sendMessage = async () => {
    const userText = chatInput.value.trim();
    if (!userText) return;

    const userChat = createChatElement(`<div class="chat-content">
                                            <div class="chat-details">
                                                <img src="/static/images/user.jpg" alt="user-img">
                                                <p>${userText}</p>
                                            </div>
                                        </div>`, "outgoing");
    chatContainer.appendChild(userChat);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);

    chatInput.value = "";

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: userText, chat_history: [] })  // You can manage chat history here if needed
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        const botResponse = data.answer;

        const botChat = createChatElement(`<div class="chat-content">
                                                <div class="chat-details">
                                                    <img src="/static/images/chatbot.png" alt="chatbot-img">
                                                    <p>${botResponse}</p>
                                                </div>
                                            </div>`, "incoming");
        chatContainer.appendChild(botChat);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);

        localStorage.setItem("all-chats", chatContainer.innerHTML);
    } catch (error) {
        console.error("Error while sending message:", error);
        const errorChat = createChatElement(`<div class="chat-content">
                                                 <div class="chat-details">
                                                     <img src="/static/images/chatbot.png" alt="chatbot-img">
                                                     <p class="error">Error: Unable to fetch response.</p>
                                                 </div>
                                             </div>`, "incoming");
        chatContainer.appendChild(errorChat);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    }
};



const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const userChat = createChatElement(`<div class="chat-content">
                                            <div class="chat-details">
                                                <img src="/static/images/user.jpg" alt="user-img">
                                                <p>File uploaded: ${file.name}</p>
                                            </div>
                                        </div>`, "outgoing");
    chatContainer.appendChild(userChat);
    chatContainer.scrollTo(0, chatContainer.scrollHeight);

    try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/upload", {  // Changed from /upload_file to /upload
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Response from server:", data);

        const botResponse = data.message;  // Changed to data.message based on your Flask endpoint

        const botChat = createChatElement(`<div class="chat-content">
                                                <div class="chat-details">
                                                    <img src="/static/images/chatbot.png" alt="chatbot-img">
                                                    <p>${botResponse}</p>
                                                </div>
                                            </div>`, "incoming");
        chatContainer.appendChild(botChat);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);

        localStorage.setItem("all-chats", chatContainer.innerHTML);
    } catch (error) {
        console.error("Error while uploading file:", error);
        const errorChat = createChatElement(`<div class="chat-content">
                                                 <div class="chat-details">
                                                     <img src="/static/images/chatbot.png" alt="chatbot-img">
                                                     <p class="error">Error: Unable to upload file.</p>
                                                 </div>
                                             </div>`, "incoming");
        chatContainer.appendChild(errorChat);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    }
};

// New image upload handler
const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const imgElement = document.createElement('img');
        imgElement.src = e.target.result;
        imgElement.alt = 'Uploaded Image';
        imgElement.classList.add('chat-image');

        // Create the user chat bubble with the image
        const userChat = createChatElement(`<div class="chat-content">
                                                <div class="chat-details">
                                                    <img src="/static/images/user.jpg" alt="user-img">
                                                </div>
                                            </div>`, "outgoing");
        userChat.querySelector('.chat-details').appendChild(imgElement);
        chatContainer.appendChild(userChat);
        chatContainer.scrollTo(0, chatContainer.scrollHeight);
    };
    reader.readAsDataURL(file);
};

const deleteChats = () => {
    if (confirm("Are you sure you want to delete all the chats?")) {
        localStorage.removeItem("all-chats");
        showDefaultText();
    }
};

const handleSendClick = () => {
    sendMessage();
};

const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
        e.preventDefault();
        sendMessage();
    }
};

loadDataFromLocalStorage();
sendButton.addEventListener("click", handleSendClick);
deleteButton.addEventListener("click", deleteChats);
chatInput.addEventListener("keydown", handleKeyDown);

// Handling the upload button click to trigger the file input
uploadButton.addEventListener("click", () => uploadInput.click());

// Handling the file input change to handle file upload or image upload
uploadInput.addEventListener("change", handleFileUpload);

// Image upload button behavior
document.querySelector("#add-btn").addEventListener("click", () => {
    document.querySelector("#image-input").click();
});

document.querySelector("#image-input").addEventListener("change", handleImageUpload);
