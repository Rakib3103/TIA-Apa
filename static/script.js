const chatInput = document.querySelector("#chat-input");
const sendButton = document.querySelector("#send-btn");
const chatContainer = document.querySelector(".chat-container");
const themeButton = document.querySelector("#theme-btn");
const deleteButton = document.querySelector("#delete-btn");
const uploadButton = document.querySelector("#upload-btn");
const uploadInput = document.querySelector("#upload-input"); // Corrected ID reference

const loadDataFromLocalStorage = () => {
    const themeColor = localStorage.getItem("themeColor") || "light_mode";

    document.body.classList.toggle("light-mode", themeColor === "light_mode");
    themeButton.innerText = themeColor === "light_mode" ? "dark_mode" : "light_mode";

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
                            <h1>TIA APA</h1>
                            <p>Ask anything to APA.<br> Your chat will be displayed here.</p>
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
        const response = await fetch("/query", {  // Changed from /get_response to /query
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: userText, chat_history: [] })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Response from server:", data);

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

const deleteChats = () => {
    if (confirm("Are you sure you want to delete all the chats?")) {
        localStorage.removeItem("all-chats");
        showDefaultText();
    }
};

const toggleTheme = () => {
    const themeColor = document.body.classList.contains("light-mode") ? "dark_mode" : "light_mode";
    document.body.classList.toggle("light-mode");
    themeButton.innerText = themeColor;
    localStorage.setItem("themeColor", themeColor);
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
themeButton.addEventListener("click", toggleTheme);
chatInput.addEventListener("keydown", handleKeyDown);

// Handling the upload button click to trigger the file input
uploadButton.addEventListener("click", () => uploadInput.click());

// Handling the file input change to handle file upload
uploadInput.addEventListener("change", handleFileUpload);
