
document.addEventListener("DOMContentLoaded", () => {
    const $ = (id) => document.getElementById(id);

    let currentLanguage = "en";
    let allRooms = [];

    const languageButton = $("languageButton");
    const roomList = $("roomList");
    const roomStatus = $("roomStatus");
    const roomSearch = $("roomSearch");
    const bookingForm = $("bookingForm");
    const bookingStatus = $("bookingStatus");
    const chatForm = $("chatForm");
    const chatInput = $("chatInput");
    const chatMessages = $("chatMessages");
    const serviceForm = $("serviceForm");
    const serviceStatus = $("serviceStatus");

    const today = new Date();
    const todayString = [
        today.getFullYear(),
        String(today.getMonth() + 1).padStart(2, "0"),
        String(today.getDate()).padStart(2, "0")
    ].join("-");

    // Set minimum selectable dates
    ["searchCheckIn", "searchCheckOut", "checkIn", "checkOut"].forEach(id => {
        if ($(id)) $(id).min = todayString;
    });

    function showStatus(element, message, isError = false) {
        if (!element) return;

        element.textContent = message;
        element.style.color = isError ? "#dc2626" : "#2563eb";
    }

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[char]);
    }

    async function apiRequest(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        return data;
    }

    // ---------------------------------
    // 1. HINDI / ENGLISH LANGUAGE
    // ---------------------------------

    function translatePage() {
        document.documentElement.lang = currentLanguage;

        document.querySelectorAll("[data-en][data-hi]").forEach(element => {
            element.textContent =
                element.getAttribute(`data-${currentLanguage}`);
        });

        if (languageButton) {
            languageButton.textContent =
                currentLanguage === "en" ? "हिन्दी" : "English";
        }

        if (chatInput) {
            chatInput.placeholder = currentLanguage === "en"
                ? "Type your question..."
                : "अपना सवाल लिखें...";
        }

        loadRooms();
    }

    if (languageButton) {
        languageButton.addEventListener("click", () => {
            currentLanguage = currentLanguage === "en" ? "hi" : "en";
            translatePage();
        });
    }

    // ---------------------------------
    // 2. LOAD AND SEARCH ROOMS
    // ---------------------------------

    async function loadRooms() {
        if (!roomList) return;

        showStatus(
            roomStatus,
            currentLanguage === "en"
                ? "Loading rooms..."
                : "कमरे लोड हो रहे हैं..."
        );

        const params = new URLSearchParams();

        const checkIn = $("searchCheckIn")?.value || "";
        const checkOut = $("searchCheckOut")?.value || "";
        const budget = $("budget")?.value || "";

        if (checkIn) params.set("check_in", checkIn);
        if (checkOut) params.set("check_out", checkOut);
        if (budget) params.set("budget", budget);

        try {
            const data = await apiRequest(
                `/api/rooms?${params.toString()}`
            );

            allRooms = data.rooms || [];
            displayRooms(allRooms);

            showStatus(
                roomStatus,
                currentLanguage === "en"
                    ? `${allRooms.length} room(s) found.`
                    : `${allRooms.length} कमरे मिले।`
            );

        } catch (error) {
            roomList.innerHTML = "";

            showStatus(
                roomStatus,
                error.message,
                true
            );
        }
    }

    function displayRooms(rooms) {
        if (!roomList) return;

        if (!rooms.length) {
            roomList.innerHTML = `
                <p>
                    ${currentLanguage === "en"
                        ? "No rooms found for your search."
                        : "आपकी खोज के अनुसार कोई कमरा नहीं मिला।"}
                </p>
            `;
            return;
        }

        roomList.innerHTML = rooms.map(room => {
            const image = room.image_url || "";

            return `
                <article class="room-card">

                    ${image ? `
                        <img
                            class="room-image"
                            src="${escapeHTML(image)}"
                            alt="${escapeHTML(room.name)}"
                            onerror="this.style.display='none'"
                        >
                    ` : ""}

                    <div class="room-card-content">

                        <span class="room-number">
                            ${currentLanguage === "en"
                                ? "ROOM"
                                : "कमरा"} #${room.id}
                        </span>

                        <h3>${escapeHTML(room.name)}</h3>

                        <p class="room-type">
                            ${escapeHTML(room.room_type)}
                        </p>

                        <p>${escapeHTML(room.description || "")}</p>

                        <p class="room-amenities">
                            <strong>
                                ${currentLanguage === "en"
                                    ? "Facilities:"
                                    : "सुविधाएँ:"}
                            </strong>
                            ${escapeHTML(room.amenities)}
                        </p>

                        <p>
                            ${currentLanguage === "en"
                                ? "Capacity:"
                                : "क्षमता:"}
                            ${room.capacity}
                            ${currentLanguage === "en"
                                ? "guests"
                                : "मेहमान"}
                        </p>

                        <p class="room-price">
                            ₹${Number(room.price).toLocaleString("en-IN")}
                            <small>
                                / ${currentLanguage === "en"
                                    ? "night"
                                    : "रात"}
                            </small>
                        </p>

                        <button
                            type="button"
                            class="primary-button book-room-button"
                            data-room-id="${room.id}"
                        >
                            ${currentLanguage === "en"
                                ? "Book This Room"
                                : "कमरा बुक करें"}
                        </button>

                    </div>
                </article>
            `;
        }).join("");

        // Fill booking dropdown
        const roomSelect = $("roomId");

        if (roomSelect) {
            const previousValue = roomSelect.value;

            roomSelect.innerHTML = `
                <option value="">
                    ${currentLanguage === "en"
                        ? "Select a room"
                        : "कमरा चुनें"}
                </option>
                ${rooms.map(room => `
                    <option value="${room.id}">
                        ${escapeHTML(room.name)} -
                        ₹${Number(room.price).toLocaleString("en-IN")}
                    </option>
                `).join("")}
            `;

            if (rooms.some(room => String(room.id) === previousValue)) {
                roomSelect.value = previousValue;
            }
        }
    }

    if (roomSearch) {
        roomSearch.addEventListener("submit", event => {
            event.preventDefault();
            loadRooms();
        });
    }

    // Book button on each room card
    if (roomList) {
        roomList.addEventListener("click", event => {
            const button = event.target.closest(".book-room-button");

            if (!button) return;

            const roomSelect = $("roomId");

            if (roomSelect) {
                roomSelect.value = button.dataset.roomId;
            }

            const checkIn = $("searchCheckIn")?.value;
            const checkOut = $("searchCheckOut")?.value;

            if (checkIn && $("checkIn")) {
                $("checkIn").value = checkIn;
            }

            if (checkOut && $("checkOut")) {
                $("checkOut").value = checkOut;
            }

            $("booking")?.scrollIntoView({
                behavior: "smooth"
            });
        });
    }

    // ---------------------------------
    // 3. ROOM BOOKING
    // ---------------------------------

    if (bookingForm) {
        bookingForm.addEventListener("submit", async event => {
            event.preventDefault();

            showStatus(
                bookingStatus,
                currentLanguage === "en"
                    ? "Processing booking..."
                    : "बुकिंग की जा रही है..."
            );

            const bookingData = {
                guest_name: $("guestName")?.value.trim(),
                email: $("email")?.value.trim(),
                phone: $("phone")?.value.trim(),
                room_id: $("roomId")?.value,
                check_in: $("checkIn")?.value,
                check_out: $("checkOut")?.value,
                guests: $("guests")?.value
            };

            try {
                const result = await apiRequest("/api/bookings", {
                    method: "POST",
                    body: JSON.stringify(bookingData)
                });

                showStatus(
                    bookingStatus,
                    currentLanguage === "en"
                        ? `Booking confirmed! Reference: ${result.booking_ref}. Total: ₹${Number(result.total_amount).toLocaleString("en-IN")} for ${result.nights} night(s).`
                        : `बुकिंग कन्फर्म! बुकिंग नंबर: ${result.booking_ref}। कुल राशि: ₹${Number(result.total_amount).toLocaleString("en-IN")}। कुल रातें: ${result.nights}।`
                );

                bookingForm.reset();

                loadRooms();

            } catch (error) {
                showStatus(
                    bookingStatus,
                    error.message,
                    true
                );
            }
        });
    }

    // ---------------------------------
    // 4. AI CHATBOT
    // ---------------------------------

    function addMessage(message, sender) {
        if (!chatMessages) return;

        const messageElement = document.createElement("div");

        messageElement.className =
            sender === "user"
                ? "message user-message"
                : "message bot-message";

        // textContent prevents HTML injection
        messageElement.textContent = message;

        chatMessages.appendChild(messageElement);

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendChatMessage(message) {
        if (!message.trim()) return;

        addMessage(message, "user");

        if (chatInput) chatInput.value = "";

        const loadingMessage = currentLanguage === "en"
            ? "Please wait..."
            : "कृपया इंतजार करें...";

        addMessage(loadingMessage, "bot");

        const lastMessage = chatMessages?.lastElementChild;

        try {
            const result = await apiRequest("/api/chat", {
                method: "POST",
                body: JSON.stringify({
                    message: message,
                    language: currentLanguage
                })
            });

            if (lastMessage) {
                lastMessage.textContent = result.reply;
            }

        } catch (error) {
            if (lastMessage) {
                lastMessage.textContent =
                    currentLanguage === "en"
                        ? "Sorry, chatbot is temporarily unavailable."
                        : "माफ कीजिए, चैटबॉट अभी उपलब्ध नहीं है।";
            }
        }
    }

    if (chatForm) {
        chatForm.addEventListener("submit", event => {
            event.preventDefault();

            const message = chatInput?.value || "";

            sendChatMessage(message);
        });
    }

    // Quick question buttons
    document.querySelectorAll(".quick-question").forEach(button => {
        button.addEventListener("click", () => {
            const question = button.dataset.question || button.textContent;
            sendChatMessage(question);
        });
    });

    // ---------------------------------
    // 5. GUEST SERVICES
    // ---------------------------------

    if (serviceForm) {
        serviceForm.addEventListener("submit", async event => {
            event.preventDefault();

            showStatus(
                serviceStatus,
                currentLanguage === "en"
                    ? "Submitting request..."
                    : "आपका अनुरोध भेजा जा रहा है..."
            );

            const serviceData = {
                guest_name: $("serviceName")?.value.trim(),
                room_number: $("roomNumber")?.value.trim(),
                request_type: $("requestType")?.value,
                details: $("serviceDetails")?.value.trim()
            };

            try {
                const result = await apiRequest(
                    "/api/service-requests",
                    {
                        method: "POST",
                        body: JSON.stringify(serviceData)
                    }
                );

                showStatus(
                    serviceStatus,
                    currentLanguage === "en"
                        ? `Request submitted successfully! Request ID: ${result.request_id}`
                        : `आपका अनुरोध सफलतापूर्वक भेजा गया! अनुरोध ID: ${result.request_id}`
                );

                serviceForm.reset();

            } catch (error) {
                showStatus(
                    serviceStatus,
                    error.message,
                    true
                );
            }
        });
    }

    // ---------------------------------
    // 6. INITIALIZE WEBSITE
    // ---------------------------------

    translatePage();

    if (chatMessages && chatMessages.children.length === 0) {
        addMessage(
            currentLanguage === "en"
                ? "Hello! Welcome to SmartStay AI. Ask me about rooms, prices, booking or hotel facilities."
                : "नमस्ते! SmartStay AI में आपका स्वागत है। कमरे, किराए, बुकिंग या होटल की सुविधाओं के बारे में पूछें।",
            "bot"
        );
    }
});
