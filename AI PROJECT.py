import re
import PIL.Image
import streamlit as st
import google.generativeai as Genai
import speech_recognition as sr
import smtplib
from email.message import EmailMessage
import uuid
import mysql.connector
import pandas as pd
from datetime import datetime
import base64

# Set Streamlit Page Config at the very top
st.set_page_config(page_title="Railway Complaint Bot", page_icon="\U0001F686", layout="wide")

# Configure Google API Key
GOOGLE_API_KEY = "AIzaSyChMZvjfs_WJSfrfUi9R2Url1hVmqiS5qo"  # Replace with your actual API key
Genai.configure(api_key=GOOGLE_API_KEY)
model = Genai.GenerativeModel('gemini-1.5-flash')

# MySQL Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Rajesh#2005",  # Replace with your actual DB password
    database="raiwaycomplaint_db",
    auth_plugin="mysql_native_password"
)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        age INT,
        email VARCHAR(255),
        complaint TEXT,
        category VARCHAR(255),
        status VARCHAR(50),
        uid VARCHAR(50),
        pnr_uts VARCHAR(50),
        incident_date DATE,
        forwarded_by VARCHAR(255),  -- New field for storing forwarded email
        reason TEXT  -- New field for storing the reason for approval/rejection
    )
""")
conn.commit()

background_image_url = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExc21hZmtldDhjNzUxd3oycGdwdHV4dTE0d2ExNGYwNTZwYWJmYXJlbiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/6xlGmS4l53Lfa/giphy.gif"

# Inject custom CSS for full-screen background
st.markdown(f"""
    <style>
        .stApp {{
            background: url("{background_image_url}") no-repeat center center fixed;
            background-size: cover;
        }}
        .stTextInput, .stNumberInput, .stSelectbox, .stRadio {{
            background-color: rgba(255, 255, 255, 0.8); /* Semi-transparent background */
            border-radius: 10px;
            padding: 10px;
        }}
        h2 {{
            color: white;
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
        }}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        @keyframes moveText {
            from {
                transform: translateX(100%);
            }
            to {
                transform: translateX(-100%);
            }
        }
        .animated-text {
            display: inline-block;
            white-space: nowrap;
            animation: moveText 10s linear infinite;
            font-size: 16000px;
            font-weight: bold;
            color: #FF5733;
        }
        .marquee-container {
            width: 100%;
            overflow: hidden;
            white-space: nowrap;
        }
    </style>
    <div class="marquee-container">
        <p class='animated-text'>Welcome to Railway Query Complaint Bot!</p>
    </div>
""", unsafe_allow_html=True)



# Function to classify complaints
def classify_complaint(text):
    categories = {
        "STAFF BEHAVIOUR": ["Staff – Behaviour"],
        "SECURITY": ["Smoking", "Drinking Alcohol/Narcotics", "Theft of Passengers' Belongings", "Snatching", "Harassment", "Others"],
        "COACH-CLEANLINESS": ["Toilets", "Cockroach", "Rodents", "Coach-Interior", "Others"],
        "ELECTRICAL-EQUIPMENT": ["Air Conditioner", "Fans", "Lights"],
        "CORRUPTION/BRIBERY": ["Corruption/Bribery"],
        "GOODS": ["Booking", "Delivery", "Overcharging", "Staff Not Available", "Others"],
        "CATERING AND VENDING SERVICES": ["Overcharging", "Service Quality", "Food Quantity", "Food Quality", "Food and Water Not Available", "Others"],
        "MEDICAL ASSISTANCE": ["Medical Assistance"],
        "WATER AVAILABILITY": ["Drinking Water at Platform", "Packaged Drinking Water", "Rail Neer", "Water Vending Machine", "Retiring Room", "Waiting Room", "Toilet", "Others"],
        "MISCELLANEOUS": ["Miscellaneous"]
    }
    
    text_lower = text.lower()
    
    for category, sub_categories in categories.items():
        for sub_category in sub_categories:
            if sub_category.lower() in text_lower:
                return category, sub_category
    
    return "Other", "Uncategorized"

# Define station emails
station_emails = {
    "New Delhi": "ndls@railway.com",
    "Mumbai Central": "mumbai@railway.com",
    "Chennai Central": "chennai@railway.com",
    "Kolkata Howrah": "howrah@railway.com",
    "Bengaluru KSR BENGALURU": "tifcsbc@irctc.com"
}

# 📧 Email Credentials (App Passwords)
EMAIL_CREDENTIALS = {
    "rajeshms9845@gamil.com": "jvos ffrn nsxx jnih",
    "rajraiesh5@gmail.com":"nugg ddhk qadr rdsi"

}

# 📧 Email recipients based on category
CATEGORY_EMAILS = {
    "STAFF BEHAVIOUR": "rajraiesh5@gmail.com",
    "SECURITY": "nishithr2005@gmail.com",
    "COACH-CLEANLINESS": "rajraiesh5@gmail.com",
    "ELECTRICAL-EQUIPMENT": "rajraiesh54@gmail.com",
    "CORRUPTION/BRIBERY": "sagar2005nayak@gmail.com",
    "GOODS": "vi@gmail.com",
    "CATERING AND VENDING SERVICES": "mohitv9110@gmail.com",
    "MEDICAL ASSISTANCE": "manjushreemr18@gmail.com",
    "WATER AVAILABILITY": "sphalguna17@gmail.com",
    "MISCELLANEOUS": "sn3951418@gmail.com"
}

def send_complaint_email(category, subcategories, complaint_text, user_email, pnr_number):
    recipient_email = CATEGORY_EMAILS.get(category, "tshree4179@gmail.com")
    sender_email = recipient_email
    sender_password = EMAIL_CREDENTIALS.get(sender_email, "")
    
    if not sender_password:
        st.error(f"❌ No password found for {sender_email}")
        return
    
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = f"🚆 New Railway Complaint - {category}"
    
    subcategories_str = ", ".join(subcategories)
    msg.set_content(f"""
    🚨 New Complaint Submitted 🚨
    
    📂 Category: {category}
    🗂 Subcategories: {subcategories_str}
    📝 Complaint Details: {complaint_text}
    📧 User Email: {user_email}
    🎟 PNR Number: {pnr_number}

    Please take necessary action.

    Regards,  
    Railway Complaint System
    """, charset="utf-8")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        st.success(f"✅ Email sent successfully to {recipient_email} for category {category}")
    except Exception as e:
        st.error(f"❌ Failed to send email to {recipient_email}: {e}")

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["Submit Complaint", "Admin Panel", "Check Complaint Status"])

if menu == "Submit Complaint":
    # User details
    name = st.text_input("Your Name").strip()
    age = st.number_input("Your Age", min_value=1, max_value=120)
    email = st.text_input("Your Email").strip()

    pnr_uts_option = st.radio("Provide either PNR or UTS number:", ("PNR Number", "UTS Number"))
    pnr_uts_number = st.text_input(f"Enter your {pnr_uts_option}").strip()
    incident_date = st.date_input("Incident Date", datetime.today())

    # 🚉 Select Railway Station
    station = st.selectbox("Select the Station Related to Your Complaint", list(station_emails.keys()))

    def is_valid_email(email):
        return re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)

    input_option = st.radio("How do you want to provide feedback?", ("Type", "Record Voice"))
    input_msg = ""
    if input_option == "Type":
        input_msg = st.text_area("Customer Feedback:", key="input").strip()
    else:
        record_button = st.button("\U0001F3A4 Record Voice")
        if record_button:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("Recording... Speak now!")
                audio_data = recognizer.listen(source)
            try:
                input_msg = recognizer.recognize_google(audio_data)
                st.text_area("Converted Voice to Text:", input_msg)
            except sr.UnknownValueError:
                st.warning("Could not understand the audio.")
                input_msg = ""
            except sr.RequestError:
                st.warning("Speech recognition service error.")
                input_msg = ""

    uploaded_file = st.file_uploader("\U0001F4F7 Upload an image (if applicable)...", type=["jpg", "png", "jpeg"])
    image = None
    if uploaded_file is not None:
        image = PIL.Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("📩 Submit Complaint"):
        if not name or not email or not pnr_uts_number or not input_msg:
            st.warning("⚠️ Please fill in all fields including PNR/UTS number and feedback.")
        elif not is_valid_email(email):
            st.warning("⚠️ Invalid email format. Please enter a valid email.")
        else:
            response = model.generate_content([
                "Analyze the uploaded image and compare it with the provided text. If the complaint matches the evidence in the image, return 'Approved'. If there is a mismatch, return 'Rejected'. Also, classify the complaint under a relevant category.",
                input_msg,
                image
            ])

            category, sub_category = classify_complaint(input_msg)
            complaint_id = str(uuid.uuid4())[:8]
            status = "Approved" if "Approved" in response.text else "Rejected"

            # Get the email for the selected station
            forwarded_by = station_emails[station]

            # Store the reason for approval/rejection
            reason = response.text if status == "Rejected" else "Approved based on evidence."

            try:
                cursor.execute("""
                    INSERT INTO complaints (name, age, email, complaint, category, status, uid, pnr_uts, incident_date, forwarded_by, reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, age, email, input_msg, category, status, complaint_id, pnr_uts_number, incident_date, forwarded_by, reason))
                conn.commit()
                st.success("✅ Complaint Submitted Successfully!")

                # Send email notification
                send_complaint_email(category, [sub_category], input_msg, email, pnr_uts_number)

            except mysql.connector.Error as err:
                st.error(f"❌ MySQL Error: {err}")

            st.subheader("📝 Analysis Result:")
            if status == "Rejected":
                st.write("❌ Complaint Status: Rejected")
                st.write("Reason: " + reason)  # Display the reason for rejection
            else:
                # Only show category and sub-category if the complaint is approved
                st.subheader("📌 Complaint Category:")
                st.write(category)
                st.subheader("📌 Complaint Sub-Category:")
                st.write(sub_category)
                st.subheader("📋 Complaint Status:")
                st.write(status)
                st.subheader("🔑 Unique ID:")
                st.write(complaint_id)

elif menu == "Admin Panel":
    st.subheader("🔑 Admin Panel")
    admin_user = st.text_input("Admin Username")
    admin_pass = st.text_input("Admin Password", type="password")

    if st.button("Login"):
        if admin_user == "admin" and admin_pass == "admin123":
            st.success("✅ Admin Access Granted")

            # Display complaints from the database
            cursor.execute("""
                SELECT name, age, email, complaint, category, status, uid, pnr_uts, incident_date, forwarded_by, reason
                FROM complaints
            """)
            complaints = cursor.fetchall()
            if complaints:
                df = pd.DataFrame(complaints, columns=["Name", "Age", "Email", "Complaint", "Category", "Status", "UID", "PNR/UTS", "Incident Date", "Forwarded By", "Reason"])

                st.write(df)

                st.download_button("📥 Download Excel", df.to_csv(index=False).encode("utf-8"), "complaints.csv", "text/csv")
            else:
                st.write("No complaints available.")

elif menu == "Check Complaint Status":
    st.subheader("🔍 Check Complaint Status")
    check_uid = st.text_input("Enter Your Complaint Unique ID")
    if st.button("Check Status"):
        cursor.execute("SELECT status, reason FROM complaints WHERE uid=%s", (check_uid,))
        result = cursor.fetchone()
        if result:
            status, reason = result  # Unpack the result into status and reason
            st.write("📋 Complaint Status: " + status)
            st.write("Reason: " + reason)  # Display the reason for approval/rejection
        else:
            st.warning("No complaint found with this ID.")

cursor.close()
conn.close()