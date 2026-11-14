from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
import secrets
import json
import urllib.request
import urllib.error
from datetime import date, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotel.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SMARTSTAY_SECRET", "dev-only-change-this-secret")
ADMIN_PASSWORD = os.environ.get("SMARTSTAY_ADMIN_PASSWORD", "ChangeMe123!")

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def initialize_database():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            capacity INTEGER NOT NULL CHECK(capacity > 0),
            amenities TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_ref TEXT NOT NULL UNIQUE,
            guest_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            room_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            guests INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        );

        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            room_number TEXT NOT NULL,
            request_type TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        room_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(rooms)").fetchall()
        }
        if "description" not in room_columns:
            db.execute(
                "ALTER TABLE rooms ADD COLUMN description TEXT NOT NULL DEFAULT ''"
            )
        if "active" not in room_columns:
            db.execute(
                "ALTER TABLE rooms ADD COLUMN active INTEGER NOT NULL DEFAULT 1"
            )
        if "image_url" not in room_columns:
            db.execute(
                "ALTER TABLE rooms ADD COLUMN image_url TEXT NOT NULL DEFAULT ''"
            )
        room_images = {
            "Standard": "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=900&q=80",
            "Deluxe": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80",
            "Suite": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=900&q=80",
            "Premium": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=900&q=80",
            "Executive": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=900&q=80",
            "Couple": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=900&q=80",
            "Honeymoon": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80",
        }
        for room_type, image_url in room_images.items():
            db.execute(
                "UPDATE rooms SET image_url=? WHERE room_type=? AND image_url=''",
                (image_url, room_type),
            )
        db.execute(
            "UPDATE rooms SET price=2000 WHERE active=1 AND price < 2000"
        )
        db.execute(
            "UPDATE rooms SET price=3500 WHERE active=1 AND price > 3500"
        )
        db.execute(
            "UPDATE rooms SET name='AI Smart Couple Room', room_type='AI Smart Couple' "
            "WHERE name='Couple Comfort Room'"
        )
        db.execute(
            "UPDATE rooms SET name='SmartStay Comfort Room', room_type='Smart Comfort' "
            "WHERE name='AI Smart Couple Room'"
        )
        db.execute(
            "UPDATE rooms SET name='AI Elite Suite', room_type='AI Elite' "
            "WHERE name='Honeymoon Suite'"
        )
        db.execute(
            "UPDATE rooms SET name='Royal Luxury Suite', room_type='Royal Luxury' "
            "WHERE name='AI Elite Suite'"
        )
        db.execute(
            "UPDATE rooms SET name='Grand Royal Room', room_type='Grand Royal' "
            "WHERE name='Executive Room'"
        )
        count = db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        if count == 0:
            rooms = [
                ("Standard Room", "Standard", 1499, 2, "Wi-Fi, TV, Queen Bed", "Comfortable room for up to two guests.", room_images["Standard"]),
                ("Deluxe AC Room", "Deluxe", 2199, 2, "AC, Wi-Fi, TV, Breakfast", "Air-conditioned room with breakfast.", room_images["Deluxe"]),
                ("Family Suite", "Suite", 3499, 4, "AC, Wi-Fi, TV, Sofa, Breakfast", "Spacious suite for families.", room_images["Suite"]),
                ("Premium Room", "Premium", 2799, 3, "AC, Wi-Fi, TV, Work Desk", "Premium room with a work desk.", room_images["Premium"])
            ]
            db.executemany("""INSERT INTO rooms
                (name, room_type, price, capacity, amenities, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", rooms)
        if db.execute(
            "SELECT COUNT(*) FROM rooms WHERE name='Grand Royal Room'"
        ).fetchone()[0] == 0:
            db.execute("""INSERT INTO rooms
                (name, room_type, price, capacity, amenities, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("Grand Royal Room", "Grand Royal", 2999, 3,
                 "AC, Wi-Fi, Smart TV, Work Desk, Mini Fridge",
                 "Elegant royal room with premium furnishings and smart controls.",
                 room_images["Executive"]))
        if db.execute(
            "SELECT COUNT(*) FROM rooms WHERE name='SmartStay Comfort Room'"
        ).fetchone()[0] == 0:
            db.execute("""INSERT INTO rooms
                (name, room_type, price, capacity, amenities, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("SmartStay Comfort Room", "Smart Comfort", 2599, 2,
                 "AC, Wi-Fi, Smart TV, King Bed, Room Service",
                 "AI-enhanced couple room with smart controls, modern comforts and room service.",
                 room_images["Couple"]))
        if db.execute(
            "SELECT COUNT(*) FROM rooms WHERE name='Royal Luxury Suite'"
        ).fetchone()[0] == 0:
            db.execute("""INSERT INTO rooms
                (name, room_type, price, capacity, amenities, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("Royal Luxury Suite", "Royal Luxury", 3500, 2,
                 "AC, Wi-Fi, Bathtub, King Bed, Breakfast, Room Service",
                 "Premium AI-managed suite with smart lighting, climate control and a luxury bathtub.",
                 room_images["Honeymoon"]))

def valid_dates(check_in, check_out):
    try:
        start = date.fromisoformat(check_in)
        end = date.fromisoformat(check_out)
        return start >= date.today() and end > start
    except (TypeError, ValueError):
        return False

def room_is_available(db, room_id, check_in, check_out):
    overlap = db.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE room_id = ? AND status = 'Confirmed'
          AND NOT (check_out <= ? OR check_in >= ?)
    """, (room_id, check_in, check_out)).fetchone()[0]
    return overlap == 0

def available_rooms(check_in=None, check_out=None):
    with get_db() as db:
        rows = db.execute("SELECT * FROM rooms WHERE active=1 ORDER BY price").fetchall()
        result = []
        for row in rows:
            room = dict(row)
            if check_in and check_out and not room_is_available(db, room["id"], check_in, check_out):
                continue
            result.append(room)
        return result

def generate_ai_reply(message, language):
    api_key = os.environ.get("SMARTSTAY_AI_API_KEY", "").strip()
    if not api_key:
        return None

    rooms = available_rooms()
    room_summary = "; ".join(
        f'{room["name"]} ({room["room_type"]}, {room["capacity"]} guests, '
        f'₹{room["price"]:.0f}, {room["amenities"]})'
        for room in rooms
    )
    response_language = "Hindi" if language == "hi" else "English"
    prompt = (
        "You are the hotel assistant for SmartStay AI. Answer briefly and "
        "helpfully using only this hotel information. "
        f"Room information: {room_summary}. "
        "Check-in is 12:00 PM and check-out is 11:00 AM. "
        f"Reply in {response_language}. "
        f"Guest message: {message}"
    )
    payload = {
        "model": os.environ.get("SMARTSTAY_AI_MODEL", "gpt-4o-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 220,
    }
    endpoint = os.environ.get(
        "SMARTSTAY_AI_ENDPOINT",
        "https://api.openai.com/v1/chat/completions",
    )
    request_obj = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=12) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, TimeoutError):
        return None

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/api/rooms")
def rooms_api():
    check_in = request.args.get("check_in", "")
    check_out = request.args.get("check_out", "")
    budget_text = request.args.get("budget", "").strip()
    if bool(check_in) != bool(check_out):
        return jsonify({"error": "Enter both check-in and check-out dates."}), 400
    if check_in and not valid_dates(check_in, check_out):
        return jsonify({"error": "Please enter valid future dates; check-out must be after check-in."}), 400
    rooms = available_rooms(check_in or None, check_out or None)
    if budget_text:
        try:
            budget = float(budget_text)
            if budget < 0:
                raise ValueError
            rooms = [r for r in rooms if r["price"] <= budget]
        except ValueError:
            return jsonify({"error": "Enter a valid non-negative budget."}), 400
    return jsonify({"rooms": rooms})

@app.post("/api/chat")
def chat_api():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    language = data.get("language", "en")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 500:
        return jsonify({"error": "Message must be 500 characters or fewer."}), 400
    text = message.lower()
    hi = language == "hi"

    if any(x in text for x in ["difference", "compare", "comparison", "तुलना"]):
        rooms = available_rooms()
        lines = [
            f"{room['name']}: ₹{room['price']:.0f}, up to {room['capacity']} guests"
            for room in rooms
        ]
        reply = (
            "कमरों की तुलना:\n" + "\n".join(lines)
            if hi else
            "Room comparison:\n" + "\n".join(lines)
        )
    elif any(x in text for x in ["recommend", "suggest", "best room", "सुझाव", "बेहतर कमरे"]):
        rooms = available_rooms()
        if rooms:
            room = min(rooms, key=lambda item: item["price"])
            reply = (
                f"आपके बजट के लिए {room['name']} अच्छा विकल्प है। इसकी रात की कीमत ₹{room['price']:.0f} है।"
                if hi else
                f"For a budget-friendly stay, I recommend {room['name']} at ₹{room['price']:.0f} per night."
            )
        else:
            reply = "फिलहाल कमरे उपलब्ध नहीं हैं।" if hi else "No rooms are currently available to recommend."
    elif any(x in text for x in ["price", "cost", "rate", "budget", "कम", "किराया", "कीमत", "दाम"]):
        rooms = available_rooms()
        if not rooms:
            reply = "फिलहाल कमरे उपलब्ध नहीं हैं।" if hi else "No rooms are currently listed."
        else:
            budget_numbers = [int(value) for value in "".join(
                char if char.isdigit() else " " for char in text
            ).split() if int(value) > 100]
            if budget_numbers:
                budget = max(budget_numbers)
                rooms = [room for room in rooms if room["price"] <= budget]
            lines = [f'{r["name"]}: ₹{r["price"]:.0f} / रात' if hi else f'{r["name"]}: ₹{r["price"]:.0f} / night' for r in rooms]
            reply = ("कमरों का डेमो किराया:\n" if hi else "Sample room prices:\n") + "\n".join(lines)
    elif any(x in text for x in ["check-in", "check in", "checkin", "चेक इन", "चेक-इन"]):
        reply = "डेमो चेक-इन समय दोपहर 12 बजे है।" if hi else "Demo check-in time is 12:00 PM."
    elif any(x in text for x in ["check-out", "checkout", "check out", "चेक आउट", "चेक-आउट"]):
        reply = "डेमो चेक-आउट समय सुबह 11 बजे है।" if hi else "Demo check-out time is 11:00 AM."
    elif any(x in text for x in ["wifi", "wi-fi", "breakfast", "facility", "facilities", "amenities", "सुविधा", "वाईफाई", "नाश्ता"]):
        reply = "कमरे के अनुसार Wi-Fi, TV, AC और कुछ कमरों में नाश्ता उपलब्ध है।" if hi else "Amenities vary by room and may include Wi-Fi, TV, AC and breakfast."
    elif any(x in text for x in ["family", "children", "kids", "परिवार", "बच्च"]):
        rooms = available_rooms()
        family_rooms = sorted(
            [room for room in rooms if room["capacity"] >= 3 or "Suite" in room["room_type"]],
            key=lambda room: room["price"],
        )
        if family_rooms:
            room = family_rooms[0]
            reply = (
                f"परिवार के लिए {room['name']} अच्छा विकल्प है। इसमें {room['capacity']} मेहमान रह सकते हैं।"
                if hi else
                f"Family Suite or higher is recommended. {room['name']} can accommodate {room['capacity']} guests and costs ₹{room['price']:.0f} per night."
            )
        else:
            reply = "कोई उपयुक्त फैमिली रूम उपलब्ध नहीं है।" if hi else "No suitable family room is currently available."
    elif any(x in text for x in ["available", "availability", "room", "rooms", "कमरा", "कमरे", "उपलब्ध"]):
        rooms = available_rooms()
        names = ", ".join(r["name"] for r in rooms) if rooms else ("कोई कमरा सूचीबद्ध नहीं है" if hi else "No rooms are listed")
        reply = ("अभी सूची में उपलब्ध कमरे: " if hi else "Rooms currently listed: ") + names + (". तारीख के अनुसार उपलब्धता जाँचने के लिए ऊपर तारीख चुनें।" if hi else ". Select dates above to check date-specific availability.")
    elif any(x in text for x in ["cancel", "modify", "change booking", "रद्द", "बुकिंग बदल"]):
        reply = (
            "अपनी बुकिंग रद्द या बदलने के लिए Admin डैशबॉर्ड या होटल सहायता से बुकिंग ID साझा करें।"
            if hi else
            "To cancel or modify a booking, contact hotel support with your booking reference so the reservation can be updated."
        )
    elif any(x in text for x in ["service", "services", "housekeeping", "cleaning", "maintenance", "available for guest", "सेवा", "सुविधा", "साफाई"]):
        reply = (
            "Guest services में Room Cleaning, Food Service, Maintenance, Laundry, Airport Pickup, "
            "Travel Assistance, Wake-up Call, Luggage Assistance और Other सहायता शामिल हैं। "
            "Guest Services form में अपनी details भरकर request submit करें।"
            if hi else
            "Available guest services are Room Cleaning, Food Service, Maintenance, Laundry, Airport Pickup, "
            "Travel Assistance, Wake-up Call, Luggage Assistance, and Other assistance. "
            "Open the Guest Services form, enter your room and request details, then submit it."
        )
    elif any(x in text for x in ["parking", "park", "pickup", "airport", "पार्किंग", "एयरपोर्ट"]):
        reply = (
            "पार्किंग और एयरपोर्ट पिकअप की उपलब्धता बुकिंग से पहले होटल टीम से पुष्टि करें।"
            if hi else
            "Please confirm parking and airport pickup availability with the hotel team before arrival."
        )
    elif any(x in text for x in ["payment", "pay", "refund", "भुगतान", "रिफंड"]):
        reply = (
            "भुगतान और रिफंड की पुष्टि बुकिंग विवरण के आधार पर होटल टीम द्वारा की जाती है।"
            if hi else
            "Payment and refund details are confirmed by the hotel team based on the booking and applicable cancellation policy."
        )
    elif any(x in text for x in ["how to book", "booking process", "book a room", "बुकिंग कैसे", "कमरा कैसे बुक"]):
        reply = (
            "Booking section में नाम, ईमेल, फोन, room, check-in, check-out और guest count भरें। फिर Confirm Booking दबाएँ।"
            if hi else
            "Open the Booking section, enter your name, email, phone number, room, dates, and guest count, then select Confirm Booking."
        )
    elif any(x in text for x in ["morning", "same day", "today", "आज", "सुबह"]):
        reply = (
            "आज की booking के लिए check-in की तारीख आज चुनें, subject to room availability। सुबह check-in भी selected room और hotel policy पर आधारित होगा।"
            if hi else
            "For a same-day booking, select today's date in check-in, subject to availability. Morning check-in depends on the selected room and hotel policy."
        )
    elif any(x in text for x in ["one person", "single", "solo", "1 guest", "एक व्यक्ति"]):
        rooms = available_rooms()
        rooms = [room for room in rooms if room["capacity"] >= 1]
        if rooms:
            room = min(rooms, key=lambda item: item["price"])
            reply = (
                f"Solo guest के लिए {room['name']} अच्छा विकल्प है। यह ₹{room['price']:.0f} प्रति रात है।"
                if hi else
                f"For one guest, I recommend {room['name']} at ₹{room['price']:.0f} per night."
            )
        else:
            reply = "फिलहाल कोई suitable room उपलब्ध नहीं है।" if hi else "No suitable room is currently available."
    elif any(x in text for x in ["2 guests", "two guests", "2 people", "couple", "दो लोग"]):
        rooms = [room for room in available_rooms() if room["capacity"] >= 2]
        if rooms:
            room = min(rooms, key=lambda item: item["price"])
            reply = (
                f"दो guests के लिए सबसे economical option {room['name']} है, जो ₹{room['price']:.0f} प्रति रात है।"
                if hi else
                f"For two guests, the most economical option is {room['name']} at ₹{room['price']:.0f} per night."
            )
        else:
            reply = "दो guests के लिए कोई suitable room उपलब्ध नहीं है।" if hi else "No suitable room is available for two guests."
    elif any(x in text for x in ["contact", "phone", "number", "संपर्क", "फोन"]):
        reply = (
            "अभी इस project में hotel contact number configure नहीं है। कृपया booking confirmation या admin panel के निर्देशों का उपयोग करें।"
            if hi else
            "A hotel contact number is not configured in this project yet. Please use your booking confirmation or the admin dashboard for reservation details."
        )
    elif any(x in text for x in ["thank", "thanks", "धन्यवाद", "थैंक"]):
        reply = "आपका स्वागत है! बाकी hotel information के लिए पूछ सकते हैं।" if hi else "You're welcome! Ask me anything else about rooms, booking, or hotel services."
    elif any(x in text for x in ["bye", "good night", "अलविदा", "फिर मिलेंगे"]):
        reply = "धन्यवाद! SmartStay AI की ओर से शुभ यात्रा।" if hi else "Thank you! Have a pleasant stay with SmartStay AI."
    elif any(x in text for x in ["hello", "hi", "hey", "नमस्ते", "नमस्कार"]):
        reply = "नमस्ते! कमरे, किराए, उपलब्धता या सुविधाओं के बारे में पूछें।" if hi else "Hello! Ask me about rooms, prices, availability or facilities."
    else:
        rooms = available_rooms()
        room_names = ", ".join(room["name"] for room in rooms)
        mentioned_room = next(
            (room for room in rooms if room["name"].lower() in text),
            None,
        )
        if mentioned_room:
            reply = (
                f"{mentioned_room['name']} में {mentioned_room['capacity']} guests तक रह सकते हैं। "
                f"Price ₹{mentioned_room['price']:.0f} प्रति रात है। Amenities: {mentioned_room['amenities']}।"
                if hi else
                f"{mentioned_room['name']} accommodates up to {mentioned_room['capacity']} guests. "
                f"The price is ₹{mentioned_room['price']:.0f} per night. Amenities: {mentioned_room['amenities']}."
            )
        else:
            budget_numbers = [
                int(value)
                for value in "".join(
                    character if character.isdigit() else " "
                    for character in text
                ).split()
                if int(value) >= 2000
            ]
            if budget_numbers and rooms:
                budget = max(budget_numbers)
                matching_rooms = [room for room in rooms if room["price"] <= budget]
                if matching_rooms:
                    names = ", ".join(room["name"] for room in matching_rooms)
                    reply = (
                        f"₹{budget:.0f} बजट में available rooms: {names}।"
                        if hi else
                        f"Rooms available within your ₹{budget:.0f} budget: {names}."
                    )
                else:
                    reply = (
                        f"₹{budget:.0f} बजट में अभी कोई room उपलब्ध नहीं है।"
                        if hi else
                        f"No room is currently available within your ₹{budget:.0f} budget."
                    )
            else:
                reply = (
                    f"मैं आपका hotel सवाल समझ रहा हूँ। SmartStay में available rooms हैं: {room_names}. "
                    "आप room name, price, amenities, booking या check-in के बारे में पूछ सकते हैं।"
                    if hi else
                    f"I can help with your stay at SmartStay AI. Available rooms are: {room_names}. "
                    "Ask about a room name, price, amenities, booking, availability, or check-in."
                )

    return jsonify({"reply": reply, "type": "hotel_assistant"})

@app.post("/api/bookings")
def create_booking():
    data = request.get_json(silent=True) or {}
    required = ["guest_name", "email", "phone", "room_id", "check_in", "check_out", "guests"]
    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error": "Please complete all booking fields."}), 400
    if not valid_dates(data["check_in"], data["check_out"]):
        return jsonify({"error": "Choose valid future dates. Check-out must be after check-in."}), 400
    try:
        room_id = int(data["room_id"])
        guests = int(data["guests"])
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid room or guest count."}), 400
    if guests < 1:
        return jsonify({"error": "At least one guest is required."}), 400

    try:
        with get_db() as db:
            room = db.execute("SELECT * FROM rooms WHERE id=? AND active=1", (room_id,)).fetchone()
            if not room:
                return jsonify({"error": "Room not found."}), 404
            if guests > room["capacity"]:
                return jsonify({"error": f'This room allows up to {room["capacity"]} guests.'}), 400
            if not room_is_available(db, room_id, data["check_in"], data["check_out"]):
                return jsonify({"error": "This room is already booked for those dates. Choose another room or dates."}), 409
            nights = (date.fromisoformat(data["check_out"]) - date.fromisoformat(data["check_in"])).days
            ref = "SSA-" + secrets.token_hex(4).upper()
            total = nights * room["price"]
            db.execute("""INSERT INTO bookings
                (booking_ref, guest_name, email, phone, room_id, check_in, check_out, guests, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ref, data["guest_name"].strip(), data["email"].strip(), data["phone"].strip(),
                 room_id, data["check_in"], data["check_out"], guests, total))
        return jsonify({"message": "Booking confirmed.", "booking_ref": ref, "total_amount": total, "nights": nights}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Could not save booking. Please try again."}), 500

@app.post("/api/service-requests")
def create_service_request():
    data = request.get_json(silent=True) or {}
    fields = ["guest_name", "room_number", "request_type", "details"]
    if any(not str(data.get(k, "")).strip() for k in fields):
        return jsonify({"error": "Please complete all service request fields."}), 400
    if len(data["details"]) > 500:
        return jsonify({"error": "Details must be 500 characters or fewer."}), 400
    with get_db() as db:
        cur = db.execute("""INSERT INTO service_requests
            (guest_name, room_number, request_type, details)
            VALUES (?, ?, ?, ?)""",
            tuple(data[k].strip() for k in fields))
        request_id = cur.lastrowid
    return jsonify({"message": "Service request submitted.", "request_id": request_id}), 201

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Incorrect password."
    return render_template("admin_login.html", error=error)

@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

@app.get("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    with get_db() as db:
        stats = {
            "rooms": db.execute("SELECT COUNT(*) FROM rooms WHERE active=1").fetchone()[0],
            "bookings": db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
            "confirmed": db.execute("SELECT COUNT(*) FROM bookings WHERE status='Confirmed'").fetchone()[0],
            "requests": db.execute("SELECT COUNT(*) FROM service_requests WHERE status='Pending'").fetchone()[0],
        }
        bookings = db.execute("""SELECT b.*, r.name AS room_name FROM bookings b
            JOIN rooms r ON r.id=b.room_id ORDER BY b.created_at DESC LIMIT 100""").fetchall()
        requests = db.execute("SELECT * FROM service_requests ORDER BY created_at DESC LIMIT 100").fetchall()
    return render_template("admin.html", stats=stats, bookings=bookings, requests=requests)

@app.post("/admin/booking/<int:booking_id>/cancel")
def cancel_booking(booking_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    with get_db() as db:
        db.execute("UPDATE bookings SET status='Cancelled' WHERE id=?", (booking_id,))
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/service/<int:request_id>/complete")
def complete_service(request_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    with get_db() as db:
        db.execute("UPDATE service_requests SET status='Completed' WHERE id=?", (request_id,))
    return redirect(url_for("admin_dashboard"))

initialize_database()

if __name__ == "__main__":
    app.run(debug=True)
