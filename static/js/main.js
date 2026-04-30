document.addEventListener('DOMContentLoaded', () => {
    // Parse Initial Markdown Summary
    const summaryDiv = document.getElementById('summaryContent');
    if (summaryDiv && summaryDiv.innerText) {
        summaryDiv.innerHTML = marked.parse(summaryDiv.innerText);
    }

    const chatForm = document.getElementById('chatForm');
    
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const inputField = document.getElementById('userInput');
            const providerSelect = document.getElementById('chat_provider');
            const chatBox = document.getElementById('chatBox');
            const typingIndicator = document.getElementById('typingIndicator');
            const sendBtn = document.getElementById('sendBtn');
            
            const question = inputField.value.trim();
            if (!question) return;

            // Render User Input
            const userHtml = `
                <div class="flex justify-end">
                    <div class="bg-indigo-600 text-white p-4 rounded-2xl rounded-tr-sm max-w-[80%] shadow-md markdown-body">
                        ${marked.parse(question)}
                    </div>
                </div>
            `;
            chatBox.insertAdjacentHTML('beforeend', userHtml);
            inputField.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
            
            // Lock UI Elements
            inputField.disabled = true;
            sendBtn.disabled = true;
            providerSelect.disabled = true;
            typingIndicator.classList.remove('hidden');

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: question,
                        provider: providerSelect.value
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    const aiHtml = `
                        <div class="flex justify-start">
                            <div class="bg-white border border-slate-200 text-slate-700 p-4 rounded-2xl rounded-tl-sm max-w-[80%] shadow-sm markdown-body">
                                ${marked.parse(data.answer)}
                            </div>
                        </div>
                    `;
                    chatBox.insertAdjacentHTML('beforeend', aiHtml);
                } else {
                    alert('Server Error: ' + (data.error || 'Unknown Error'));
                }
            } catch (error) {
                console.error('Fetch Error:', error);
                alert('A network error occurred.');
            } finally {
                // Unlock UI Elements
                typingIndicator.classList.add('hidden');
                inputField.disabled = false;
                sendBtn.disabled = false;
                providerSelect.disabled = false;
                inputField.focus();
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });
    }
});