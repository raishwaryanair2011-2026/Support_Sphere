"""
Seed script — populates the database with realistic demo data:
  - 4 support agents
  - 20 FAQs across 5 categories
  - 5 KB documents (txt files written to disk)
  - 10 sample customer accounts
  - 15 sample tickets with messages

Run from the project root (with venv active):
    python seed.py
"""
import asyncio
import os
import sys
from pathlib import Path

# ── make sure app is importable ───────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
os.chdir(Path(__file__).parent)          # so .env and support.db are found

from dotenv import load_dotenv
load_dotenv(".env", override=True)

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketMessage, TicketStatus, TicketPriority, TicketQueue
from app.models.kb import FAQ, KBDocument
from sqlalchemy import select
import uuid, datetime


# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────

AGENTS = [
    {"name": "Aishwarya R",  "email": "aish@support.com"},
    {"name": "Abhijith M S",    "email": "abhi@support.com"},
    {"name": "Pooja S",      "email": "pooja@support.com"},
    {"name": "Nanda Sree",      "email": "nanda@support.com"},
]

CUSTOMERS = [
    {"name": "Narayani A",  "email": "naru@example.com"},
    {"name": "Krishnapriya S",    "email": "krish@example.com"},
    {"name": "Gowripriya",   "email": "gowri@example.com"},
    {"name": "Jaithra G",    "email": "jaithra@example.com"},
    {"name": "Keerthana A",      "email": "keerth@example.com"},
    {"name": "Karthika S",    "email": "karth@example.com"},
    {"name": "Anjana Krishana",       "email": "anjana@example.com"},
    {"name": "Sandeep S D",    "email": "sandeep@example.com"},
    {"name": "Lina Suresh",   "email": "lina@example.com"},
    {"name": "Aarcha Kumudh",   "email": "aarcha@example.com"},
]

FAQS = [
    # Account
    {"question": "How do I reset my password?",
     "answer": "Go to the login page and click 'Forgot Password'. Enter your registered email address and you'll receive a reset link within a few minutes. Check your spam folder if it doesn't arrive.",
     "category": "Account"},
    {"question": "How do I update my email address?",
     "answer": "Log in to your account, navigate to Profile Settings, and click 'Edit Email'. You'll need to verify the new email address before the change takes effect.",
     "category": "Account"},
    {"question": "Can I have multiple accounts?",
     "answer": "No, each person should have a single account. Multiple accounts are not permitted as they can cause issues with ticket history and support continuity.",
     "category": "Account"},
    {"question": "How do I deactivate my account?",
     "answer": "To deactivate your account, please raise a support ticket from the Account category. Our team will process the request within 2 business days.",
     "category": "Account"},

    # IT Support
    {"question": "My laptop won't connect to the office WiFi. What should I do?",
     "answer": "First, try forgetting the network and reconnecting. If that doesn't work: (1) Restart your device, (2) Check if Airplane mode is off, (3) Try connecting on a different device to rule out network issues. If the problem persists, raise an IT ticket.",
     "category": "IT Support"},
    {"question": "How do I request a new software installation?",
     "answer": "Submit a ticket in the IT queue with the software name, version, and business justification. Standard software is typically installed within 1 business day. Non-standard software may require manager approval.",
     "category": "IT Support"},
    {"question": "My computer is running very slowly. What can I do?",
     "answer": "Try these steps: (1) Restart your computer, (2) Check for pending Windows/macOS updates, (3) Close unnecessary browser tabs and applications, (4) Clear your browser cache. If issues continue, submit an IT ticket for a diagnostic.",
     "category": "IT Support"},
    {"question": "How do I set up my work email on my phone?",
     "answer": "Go to your phone's Mail or Outlook app, add a new account, and enter your work email. Select 'Exchange' or 'Microsoft 365' as the account type. Use your full email as the username and your network password. Contact IT if you need the server settings.",
     "category": "IT Support"},

    # HR
    {"question": "How do I apply for annual leave?",
     "answer": "Log in to the HR portal and navigate to Leave Management. Select the dates, choose 'Annual Leave' as the type, and submit for manager approval. You'll receive an email confirmation once approved.",
     "category": "HR"},
    {"question": "Where can I find my payslips?",
     "answer": "Payslips are available in the HR portal under Payroll > My Payslips. They are uploaded on the last working day of each month. If a payslip is missing, raise an HR ticket.",
     "category": "HR"},
    {"question": "How do I update my emergency contact information?",
     "answer": "Log in to the HR portal, go to My Profile > Personal Details > Emergency Contacts. Update the information and click Save. Changes take effect immediately.",
     "category": "HR"},
    {"question": "What is the process for reporting a workplace concern?",
     "answer": "You can report concerns through the HR portal's anonymous feedback form, directly to your HR Business Partner, or via the confidential helpline listed on the intranet. All reports are handled with discretion.",
     "category": "HR"},

    # Finance
    {"question": "How do I submit an expense claim?",
     "answer": "Complete the expense claim form available on the Finance portal. Attach all receipts (photos are accepted). Submit by the 15th of the month for same-month reimbursement. Claims submitted after the 15th are processed the following month.",
     "category": "Finance"},
    {"question": "What expenses are reimbursable?",
     "answer": "Reimbursable expenses include: business travel (rail, flights, taxis), accommodation for overnight stays, client entertainment (with prior approval), and business meals. Personal expenses, alcohol without prior approval, and first-class travel are not reimbursable.",
     "category": "Finance"},
    {"question": "How long does invoice processing take?",
     "answer": "Standard invoices are processed within 30 days of receipt. Urgent invoices with valid business justification can be fast-tracked to 5 business days — raise a Finance ticket and mark it high priority.",
     "category": "Finance"},

    # Facilities
    {"question": "How do I book a meeting room?",
     "answer": "Meeting rooms can be booked through the Facilities portal or directly in Outlook/Google Calendar. Select the room as a resource when creating the meeting invite. Rooms should be released if no longer needed to allow colleagues to book them.",
     "category": "Facilities"},
    {"question": "How do I report a building maintenance issue?",
     "answer": "Submit a Facilities ticket describing the issue and its location (floor, room number). For urgent safety issues such as flooding or power outages, also call the Facilities helpdesk directly at the number posted on each floor.",
     "category": "Facilities"},
    {"question": "What are the office opening hours?",
     "answer": "The main office is open Monday to Friday, 7:00 AM – 8:00 PM. Weekend access is available with prior approval from your line manager. The reception desk is staffed 8:00 AM – 6:00 PM on weekdays.",
     "category": "Facilities"},
    {"question": "How do I request additional office supplies?",
     "answer": "Office supplies can be requested via the Facilities portal under 'Supply Request'. Standard items are fulfilled within 2 business days. For bulk orders or specialist equipment, allow up to 5 business days.",
     "category": "Facilities"},
    {"question": "Is there parking available at the office?",
     "answer": "Visitor parking is available in the ground floor car park. Employee parking requires a permit — apply through the Facilities portal. There is a waitlist for permits; current wait time is approximately 3 months.",
     "category": "Facilities"},
]

KB_DOCUMENTS = [
    {
        "title": "Password Reset Procedure",
        "category": "IT Support",
        "filename": "password_reset_procedure.txt",
        "content": """PASSWORD RESET PROCEDURE
=========================

This guide covers how to reset your password for all company systems.

SELF-SERVICE RESET (Recommended)
---------------------------------
1. Navigate to the company login page at login.company.com
2. Click "Forgot Password" below the sign-in button
3. Enter your registered work email address
4. Check your inbox for a reset link (valid for 30 minutes)
5. Click the link and enter a new password
6. Password requirements:
   - Minimum 12 characters
   - At least one uppercase letter
   - At least one number
   - At least one special character (!@#$%^&*)
   - Cannot reuse any of your last 5 passwords

ADMIN-ASSISTED RESET
--------------------
If you are locked out or unable to use self-service:
1. Contact the IT helpdesk at it@company.com
2. Provide your employee ID for verification
3. A temporary password will be sent to your personal email on file
4. You must change the temporary password on first login

MULTI-FACTOR AUTHENTICATION (MFA)
----------------------------------
All accounts require MFA. Supported methods:
- Microsoft Authenticator (recommended)
- Google Authenticator
- SMS (fallback only)

If you lose access to your MFA device, contact IT immediately.
A secondary verification process will be used to confirm your identity.

COMMON ISSUES
-------------
Q: Reset email not arriving?
A: Check spam/junk folder. Whitelist noreply@company.com. Allow up to 5 minutes.

Q: Link has expired?
A: Request a new reset link — each link is only valid for 30 minutes.

Q: Account locked after too many attempts?
A: Accounts lock after 5 failed attempts. Wait 15 minutes or contact IT to unlock.

For further assistance, raise an IT support ticket with priority set to High.
"""
    },
    {
        "title": "Remote Working Policy & VPN Guide",
        "category": "IT Support",
        "filename": "remote_working_vpn_guide.txt",
        "content": """REMOTE WORKING POLICY AND VPN GUIDE
=====================================

ELIGIBILITY
-----------
Employees may work remotely with prior agreement from their line manager.
Remote working is permitted up to 3 days per week for most roles.
Some roles require on-site presence — check your contract for details.

VPN SETUP — WINDOWS
--------------------
1. Download the company VPN client from the IT portal (Software > VPN)
2. Install with default settings
3. Open the VPN client and enter server: vpn.company.com
4. Log in with your company email and password
5. Select your closest server location
6. Click Connect

VPN SETUP — MAC
---------------
1. Download Cisco AnyConnect from the IT portal
2. Install and open the application
3. Enter vpn.company.com in the server field
4. Authenticate with company credentials
5. Accept the security certificate if prompted

VPN TROUBLESHOOTING
--------------------
Cannot connect:
- Ensure your internet connection is working
- Check your company password hasn't expired
- Try disconnecting and reconnecting
- Restart the VPN client

Slow connection through VPN:
- Connect to the nearest server location
- Disconnect non-essential devices from your home network
- Use a wired ethernet connection if possible

SECURITY REQUIREMENTS FOR REMOTE WORK
---------------------------------------
- Always connect via VPN when accessing company resources
- Do not use public WiFi without VPN active
- Lock your screen when stepping away (Win+L on Windows, Ctrl+Cmd+Q on Mac)
- Do not share your screen with household members during video calls
- Ensure your home router uses WPA2 or WPA3 encryption

EQUIPMENT
---------
Company-issued laptops must be used for all work tasks.
Personal devices may be used for email via webmail only.
If you need additional equipment (monitor, keyboard), submit a Facilities request.

For technical issues while working remotely, email it@company.com or raise a ticket.
"""
    },
    {
        "title": "Annual Leave & Absence Policy",
        "category": "HR",
        "filename": "annual_leave_policy.txt",
        "content": """ANNUAL LEAVE AND ABSENCE POLICY
================================

ANNUAL LEAVE ENTITLEMENT
-------------------------
Full-time employees: 25 days per year (plus public holidays)
Part-time employees: Pro-rated based on contracted hours
New starters: Entitlement is pro-rated from start date

Leave year runs from 1 January to 31 December.
Up to 5 days may be carried over to the following year.
Unused leave beyond 5 days is forfeited unless exceptional circumstances apply.

BOOKING ANNUAL LEAVE
---------------------
1. Log in to the HR portal
2. Go to My Leave > Request Leave
3. Select start and end dates
4. Choose "Annual Leave" from the type dropdown
5. Add any notes for your manager
6. Submit — your manager will approve or decline within 2 business days

IMPORTANT:
- Book leave at least 2 weeks in advance where possible
- Peak periods (Christmas, school holidays) require 4 weeks notice
- Minimum 2 people must remain in each team at all times
- Leave cannot be taken during the first month of employment

SICK LEAVE
----------
Day 1-3: Self-certify via the HR portal
Day 4+: A fit note from your GP is required
Return to work: Complete a return-to-work form in the HR portal

Sick pay: Full pay for first 10 days per year, then statutory sick pay applies.

EMERGENCY/COMPASSIONATE LEAVE
------------------------------
Up to 5 days paid leave for bereavement of an immediate family member.
Up to 2 days for other close relatives.
Emergency dependant care: Reasonable unpaid time — discuss with your manager.

OTHER ABSENCES
--------------
Jury duty: Paid leave for the duration
Medical appointments: Use annual leave or make up the time (agree with manager)
Maternity/Paternity: See the separate parental leave policy on the HR portal

For all leave queries, contact your HR Business Partner or raise an HR ticket.
"""
    },
    {
        "title": "Expense Claims & Reimbursement Guide",
        "category": "Finance",
        "filename": "expense_claims_guide.txt",
        "content": """EXPENSE CLAIMS AND REIMBURSEMENT GUIDE
=======================================

SUBMITTING AN EXPENSE CLAIM
-----------------------------
1. Collect all receipts (paper or digital photos are accepted)
2. Log in to the Finance portal and go to Expenses > New Claim
3. Select the expense date and category
4. Enter the amount and attach the receipt
5. Add a brief description and the business purpose
6. Submit before the 15th of the month for same-month payment

PAYMENT SCHEDULE
----------------
Claims submitted by the 15th: Paid at month end
Claims submitted after the 15th: Paid at end of following month
Payment is made directly to your bank account on file

APPROVED EXPENSE CATEGORIES
-----------------------------
Travel:
  - Rail (standard class only; first class requires director approval)
  - Flights (economy class; business class for flights over 5 hours with approval)
  - Taxis and ride-hailing (when public transport is not practical)
  - Personal vehicle mileage: 45p per mile for first 10,000 miles, 25p thereafter

Accommodation:
  - Up to £150/night in London, £100/night elsewhere
  - Book via the company travel portal where possible for better rates

Meals:
  - Breakfast: Up to £10 (only when away from home before 7am)
  - Lunch: Up to £15 (only when on business travel, not in home city)
  - Dinner: Up to £30 (when staying overnight away from home)

Client Entertainment:
  - Requires prior written approval from your line manager
  - Submit approval email with the expense claim
  - Alcohol may be included within the overall meal limit

NON-REIMBURSABLE EXPENSES
--------------------------
- Personal items (clothing, toiletries beyond overnight necessity)
- Alcohol without a client entertainment approval
- Fines (parking, speeding)
- First class travel without approval
- Expenses for non-employees unless pre-approved
- In-room movies or mini-bar items

RECEIPTS
--------
All claims over £10 require a receipt.
VAT receipts are required for all UK expenses over £25.
Lost receipts: Complete a missing receipt declaration form (available on Finance portal).

For queries, raise a Finance support ticket or email finance@company.com.
"""
    },
    {
        "title": "New Starter IT Setup Guide",
        "category": "IT Support",
        "filename": "new_starter_it_guide.txt",
        "content": """NEW STARTER IT SETUP GUIDE
===========================

Welcome! This guide will help you get set up on your first day.

YOUR EQUIPMENT
--------------
Your laptop and accessories will be ready at your desk on day one.
If anything is missing, contact IT at it@company.com immediately.

Standard equipment provided:
- Laptop (Windows or Mac depending on role)
- Power adapter
- USB-C hub or docking station
- Mouse and keyboard (hot-desking areas)

FIRST LOGIN
-----------
1. Power on your laptop
2. Connect to the guest WiFi (password on your welcome card)
3. Open a browser and go to setup.company.com
4. Enter your employee ID (provided in your welcome email)
5. Follow the prompts to set your password and configure MFA
6. Once complete, connect to the corporate WiFi using your new credentials

ESSENTIAL SOFTWARE (Pre-installed)
------------------------------------
- Microsoft 365 (Word, Excel, Outlook, Teams)
- Company VPN client
- Antivirus software
- IT asset management agent

SETTING UP EMAIL (Outlook)
---------------------------
Outlook should configure automatically when you sign in with your company account.
If it doesn't:
1. Open Outlook
2. Click Add Account
3. Enter your work email address
4. Select Microsoft 365 or Exchange
5. Enter your password when prompted

MICROSOFT TEAMS
---------------
Teams is your primary communication tool.
1. Open Teams (pre-installed or download from teams.microsoft.com)
2. Sign in with your company email
3. Your manager will add you to the relevant team channels

IT PORTAL
----------
Access the IT portal at it.company.com to:
- Request software installations
- Report issues and raise tickets
- Access the knowledge base
- Track your support tickets

NEED HELP?
----------
IT Helpdesk: it@company.com
Phone: Extension 1234 (internal) or +44 20 XXXX XXXX (external)
Walk-in support: IT desk on Floor 2, Monday to Friday 9am-5pm

Please raise a ticket for all IT issues so we can track and resolve them efficiently.
We aim to respond to all tickets within 4 business hours.
"""
    },
]

TICKETS = [
    {
        "subject": "Cannot connect to office WiFi after laptop update",
        "description": "After installing the Windows update last night, my laptop no longer connects to the corporate WiFi. It shows 'Can't connect to this network'. I've tried forgetting the network and reconnecting but it doesn't help. I need this resolved urgently as I have client calls today.",
        "status": TicketStatus.IN_PROGRESS,
        "priority": TicketPriority.HIGH,
        "queue": TicketQueue.IT,
        "customer_idx": 0,
        "messages": [
            ("agent", "Hi Narayani, thanks for raising this. This is a known issue with the recent Windows update affecting WiFi drivers. Please try this: Go to Device Manager > Network Adapters > right-click your WiFi adapter > Uninstall device. Check 'Delete the driver software' and confirm. Then restart your laptop — Windows will reinstall the correct driver automatically. Let me know if that resolves it."),
            ("customer", "I tried that and it worked! I'm now connected to the WiFi. Thank you so much for the quick help!"),
            ("agent", "Great news! I'll keep this ticket open for 24 hours in case the issue recurs. If everything is still working tomorrow, I'll close it out."),
        ]
    },
    {
        "subject": "Request for Adobe Photoshop installation",
        "description": "I need Adobe Photoshop installed on my work laptop for the upcoming marketing campaign. I'll be creating graphics and editing product images. My manager has approved this — I have the approval email from Sarah Johnson (Head of Marketing).",
        "status": TicketStatus.OPEN,
        "priority": TicketPriority.MEDIUM,
        "queue": TicketQueue.IT,
        "customer_idx": 1,
        "messages": [
            ("agent", "Hi Abhijith, thank you for your request. Could you please forward the manager approval email to it@company.com referencing this ticket number? Once we have the approval on file, we'll proceed with the installation. Adobe Creative Cloud licences are available — installation typically takes about 30 minutes."),
        ]
    },
    {
        "subject": "Payslip for March not appearing in HR portal",
        "description": "My March payslip hasn't appeared in the HR portal yet. All previous months are showing but March is missing. My colleagues' March payslips are visible on their accounts. Please could you investigate? I need it for a mortgage application.",
        "status": TicketStatus.RESOLVED,
        "priority": TicketPriority.HIGH,
        "queue": TicketQueue.HR,
        "customer_idx": 2,
        "messages": [
            ("agent", "Hi Carol, I'm sorry to hear about this — I can see why it's urgent given your mortgage application. I've checked your employee record and found a data sync error that prevented your March payslip from uploading. I've manually triggered the upload and it should now be visible in your portal. Please check and confirm."),
            ("customer", "It's showing now, thank you! The payslip is there. Really appreciate the quick resolution."),
            ("agent", "Wonderful! I'm glad we got that sorted quickly. I've also flagged this with the payroll team so they can prevent it happening to others. Closing the ticket now — don't hesitate to reach out if you need anything else."),
        ]
    },
    {
        "subject": "Expense claim from February not yet reimbursed",
        "description": "I submitted an expense claim on 12th February totalling £347.50 for travel to the Edinburgh client site. It's now been 6 weeks and I still haven't received the reimbursement. The claim reference is EXP-2024-0892. I've checked the Finance portal and the status shows 'Approved' but the payment hasn't come through.",
        "status": TicketStatus.IN_PROGRESS,
        "priority": TicketPriority.HIGH,
        "queue": TicketQueue.FINANCE,
        "customer_idx": 3,
        "messages": [
            ("agent", "Hi Daniel, I've located your claim EXP-2024-0892 and you're right — it was approved on 14th February but there appears to be an issue with the payment run. I'm escalating this to our payments team now. You should receive the £347.50 by Friday at the latest. I apologise for the delay and inconvenience."),
            ("customer", "Thank you for looking into this. Please do let me know once it's been processed."),
        ]
    },
    {
        "subject": "Air conditioning in Room 4B is not working",
        "description": "The air conditioning unit in meeting room 4B on the fourth floor has stopped working. The room is extremely hot and unusable for meetings. There are several important client meetings scheduled in this room this week. Please can this be fixed as a priority?",
        "status": TicketStatus.OPEN,
        "priority": TicketPriority.MEDIUM,
        "queue": TicketQueue.FACILITIES,
        "customer_idx": 4,
        "messages": [
            ("agent", "Hi Keerthana, thank you for reporting this. I've logged an urgent maintenance request with our building management team. An engineer is scheduled to inspect the unit tomorrow morning between 8-10am. In the meantime, I've arranged for your meetings to be moved to Room 6A on the sixth floor, which has been booked under your name for the same times. Please check your calendar for the updated room details."),
        ]
    },
    {
        "subject": "VPN not working from home — cannot access internal systems",
        "description": "I started working from home last week and I cannot get the VPN to connect. It shows 'Connection timed out' every time I try. I've installed the client from the IT portal and I'm using the server address vpn.company.com. My internet connection is working fine for other websites.",
        "status": TicketStatus.RESOLVED,
        "priority": TicketPriority.HIGH,
        "queue": TicketQueue.IT,
        "customer_idx": 5,
        "messages": [
            ("agent", "Hi Frank, the timeout error usually means a firewall is blocking the VPN port. Could you please try the following: (1) On your home router, check that port 443 is not blocked, (2) If you have a third-party firewall or antivirus, temporarily disable it and try connecting, (3) Try using your phone's mobile hotspot instead of home WiFi to test if the router is the issue."),
            ("customer", "I tried the mobile hotspot and it connected immediately! So it must be my home router."),
            ("agent", "That confirms it's your home router blocking the VPN. You'll need to log into your router's admin panel (usually 192.168.1.1) and ensure ports 443 and 1194 are not blocked. Your internet provider's support team can assist if you're unsure how to do this. Alternatively, you can continue using the mobile hotspot for VPN access. Marking this as resolved — please reopen if you need further help."),
            ("customer", "I managed to fix the router settings. VPN is working perfectly now. Thanks!"),
        ]
    },
    {
        "subject": "Request for standing desk",
        "description": "I have a medical recommendation from my GP for a standing desk due to back problems. I have the GP's letter. Could you please arrange for a height-adjustable desk to be installed at my workstation? I sit at Desk B12 on the third floor.",
        "status": TicketStatus.OPEN,
        "priority": TicketPriority.MEDIUM,
        "queue": TicketQueue.FACILITIES,
        "customer_idx": 6,
        "messages": [
            ("agent", "Hi Grace, thank you for your request. Medical-related adjustments are prioritised. Please email the GP letter to facilities@company.com with your employee ID and this ticket number in the subject line. Once received, we'll arrange for a height-adjustable desk to be installed at Desk B12. Lead time is typically 5–7 business days."),
        ]
    },
    {
        "subject": "Annual leave balance showing incorrectly",
        "description": "My annual leave balance in the HR portal shows 8 days remaining, but based on my own calculations it should be 12 days. I haven't taken any unrecorded leave. I took 5 days in January and 3 days in March, which gives me 17 days used from my 25-day entitlement. Something seems wrong.",
        "status": TicketStatus.IN_PROGRESS,
        "priority": TicketPriority.MEDIUM,
        "queue": TicketQueue.HR,
        "customer_idx": 7,
        "messages": [
            ("agent", "Hi Henry, I've reviewed your leave record and I can see the discrepancy. It appears 4 days were recorded as taken in February which you weren't aware of — this may be a system error or a misapplied adjustment from a previous year's carry-over calculation. I'm investigating with the HR system team. I'll update you within 2 business days."),
        ]
    },
    {
        "subject": "Laptop screen flickering and dimming randomly",
        "description": "For the past week, my laptop screen has been flickering and randomly going very dim. It happens both on battery and when plugged in. I've updated the display drivers but the issue persists. The laptop is a Dell XPS 15, asset tag IT-4521. This is making it very difficult to work.",
        "status": TicketStatus.OPEN,
        "priority": TicketPriority.MEDIUM,
        "queue": TicketQueue.IT,
        "customer_idx": 8,
        "messages": []
    },
    {
        "subject": "Invoice from supplier not processed after 45 days",
        "description": "Our supplier TechParts Ltd submitted an invoice on 1st March (invoice number TP-2024-441, amount £2,340) and it still hasn't been paid. They are threatening to put our account on hold which would disrupt our operations. The invoice was sent to accounts@company.com and acknowledged. Please can you investigate urgently?",
        "status": TicketStatus.IN_PROGRESS,
        "priority": TicketPriority.HIGH,
        "queue": TicketQueue.FINANCE,
        "customer_idx": 9,
        "messages": [
            ("agent", "Hi Jack, I've located invoice TP-2024-441. It appears it was received but got stuck in the approval queue due to a coding error — it was assigned to the wrong cost centre. I've corrected the coding and resubmitted for approval. Given the urgency, I've also flagged it for fast-track payment. Please inform your supplier that payment will be processed within 3 business days. I apologise for the disruption."),
            ("customer", "Thank you for the quick response. I've let TechParts know. Please do keep me updated on the payment status."),
            ("agent", "Absolutely. I'll send you a confirmation email once the payment has been issued. You should also be able to see the updated status in the Finance portal under Supplier Invoices."),
        ]
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def get_or_create_user(db: AsyncSession, name, email, role: UserRole, password="password123") -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        print(f"  → exists: {email}")
        return user
    user = User(name=name, email=email, hashed_password=hash_password(password), role=role, is_active=True)
    db.add(user)
    await db.flush()
    print(f"  ✓ created: {email}")
    return user


async def seed_kb_files(db: AsyncSession, uploader_id: int):
    os.makedirs("uploads", exist_ok=True)
    for doc_data in KB_DOCUMENTS:
        # Check if already exists
        result = await db.execute(select(KBDocument).where(KBDocument.title == doc_data["title"]))
        if result.scalar_one_or_none():
            print(f"  → KB doc exists: {doc_data['title']}")
            continue

        # Write the text file to disk
        fpath = os.path.join("uploads", doc_data["filename"])
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(doc_data["content"])

        doc = KBDocument(
            title=doc_data["title"],
            category=doc_data["category"],
            file_path=fpath,
            file_type="txt",
            status="Processing",
            chunk_count=0,
            uploaded_by=uploader_id,
        )
        db.add(doc)
        await db.flush()
        print(f"  ✓ KB doc: {doc_data['title']}")

        # Ingest into vector store (optional — skip if no Groq/ChromaDB available)
        try:
            from app.services.kb import _ingest_document
            await _ingest_document(db, doc.id)
            print(f"    → indexed ({doc.chunk_count} chunks)")
        except Exception as e:
            doc.status = "Indexed (manual)"
            doc.chunk_count = len(doc_data["content"]) // 500
            await db.flush()
            print(f"    → skipped vector indexing ({e})")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    async with AsyncSessionLocal() as db:
        print("\n── Agents ──────────────────────────────")
        agent_users = []
        for a in AGENTS:
            u = await get_or_create_user(db, a["name"], a["email"], UserRole.AGENT, "agent123")
            agent_users.append(u)

        print("\n── Customers ───────────────────────────")
        customer_users = []
        for c in CUSTOMERS:
            u = await get_or_create_user(db, c["name"], c["email"], UserRole.CUSTOMER, "customer123")
            customer_users.append(u)

        print("\n── FAQs ────────────────────────────────")
        for faq_data in FAQS:
            result = await db.execute(select(FAQ).where(FAQ.question == faq_data["question"]))
            if result.scalar_one_or_none():
                print(f"  → exists: {faq_data['question'][:50]}…")
                continue
            db.add(FAQ(**faq_data))
            print(f"  ✓ {faq_data['question'][:55]}…")

        print("\n── Knowledge Base Documents ────────────")
        admin_result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
        admin = admin_result.scalars().first()
        if admin:
            await seed_kb_files(db, admin.id)

        print("\n── Tickets ─────────────────────────────")
        for i, t_data in enumerate(TICKETS):
            customer = customer_users[t_data["customer_idx"]]
            agent = agent_users[i % len(agent_users)]

            result = await db.execute(select(Ticket).where(Ticket.subject == t_data["subject"]))
            if result.scalar_one_or_none():
                print(f"  → exists: {t_data['subject'][:50]}…")
                continue

            year = datetime.datetime.now().year
            ticket_number = f"SUP-{year}-{uuid.uuid4().hex[:6].upper()}"

            ticket = Ticket(
                ticket_number=ticket_number,
                subject=t_data["subject"],
                description=t_data["description"],
                status=t_data["status"],
                priority=t_data["priority"],
                queue=t_data["queue"],
                customer_id=customer.id,
                agent_id=agent.id,
                resolved_by=agent.id if t_data["status"] == TicketStatus.RESOLVED else None,
                closed_at=datetime.datetime.utcnow() if t_data["status"] == TicketStatus.RESOLVED else None,
            )
            db.add(ticket)
            await db.flush()

            # First message = description
            db.add(TicketMessage(
                ticket_id=ticket.id,
                sender_id=customer.id,
                sender_role="customer",
                message=t_data["description"],
            ))

            # Conversation messages
            for role, msg in t_data["messages"]:
                sender = agent if role == "agent" else customer
                db.add(TicketMessage(
                    ticket_id=ticket.id,
                    sender_id=sender.id,
                    sender_role=role,
                    message=msg,
                ))

            print(f"  ✓ [{ticket_number}] {t_data['subject'][:50]}…")

        await db.commit()
        print("\n✅ Seed complete!\n")
        print("Demo accounts (all use password shown):")
        print("  Admin:    admin@support.com     / Admin@123")
        print("  Agents:   sarah@support.com     / agent123")
        print("            james@support.com     / agent123")
        print("            priya@support.com     / agent123")
        print("            david@support.com     / agent123")
        print("  Customers:alice@example.com     / customer123")
        print("            bob@example.com       / customer123")
        print("  (and 8 more customers with password: customer123)\n")


if __name__ == "__main__":
    asyncio.run(main())