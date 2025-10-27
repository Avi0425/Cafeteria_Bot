#!/usr/bin/env python3
"""
Daily Attendance Data Fetcher
Fetches attendance data for all active users from Bennett University ERP
"""

import os
import sys
import json
import requests
import time
from datetime import datetime, timezone, timedelta

# Load environment variables from .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Load sensitive credentials from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
USER_EMAIL = os.environ.get("USER_EMAIL")
USER_PASSWORD = os.environ.get("USER_PASSWORD")

# Validate that all required environment variables are set
required_vars = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    "USER_EMAIL": USER_EMAIL,
    "USER_PASSWORD": USER_PASSWORD
}

missing_vars = [var for var, value in required_vars.items() if not value]

if missing_vars:
    print("ERROR: Required environment variables are not set!")
    print("Missing variables:", ", ".join(missing_vars))
    print("\nPlease set these environment variables:")
    print("  - TELEGRAM_BOT_TOKEN")
    print("  - TELEGRAM_CHAT_ID")
    print("  - USER_EMAIL")
    print("  - USER_PASSWORD")
    print("\nFor Railway deployment, set these in your Railway project's Variables tab.")
    sys.exit(1)

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

# API Endpoints
LOGIN_URL = "https://student.bennetterp.camu.in/login/validate"
ATTENDANCE_DATA_URL = "https://student.bennetterp.camu.in/api/Attendance/getDtaForStupage"
TIMETABLE_URL = "https://student.bennetterp.camu.in/api/Timetable/get"
CAFETERIA_MENU_URL = "https://student.bennetterp.camu.in/api/mess-management/get-student-menu-list"

def send_telegram_message(text):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set. Skipping notification.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
        print("Telegram notification sent successfully")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def login_user(email, password):
    """Login and get session + progression data"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Origin": "https://student.bennetterp.camu.in"
    })
    
    login_payload = {"dtype": "M", "Email": email, "pwd": password}
    
    try:
        response = session.post(LOGIN_URL, json=login_payload, timeout=15)
        response.raise_for_status()
        response_data = response.json().get("output", {}).get('data', {})
        
        code = response_data.get('code')
        if code in ['INCRT_CRD', 'INVALID_CRED']:
            print(f"Login failed for {email}: {code}")
            return None, None
        
        progression_data = response_data.get('progressionData', [{}])[0]
        student_id = None
        
        if 'logindetails' in response_data and 'Student' in response_data['logindetails']:
            student_id = response_data['logindetails']['Student'][0].get('StuID')
        
        return session, (progression_data, student_id)
    
    except Exception as e:
        print(f"Login error for {email}: {e}")
        return None, None

def fetch_attendance_data(session, progression_data, student_id):
    """Fetch attendance data using the stored payload structure"""
    if not progression_data or not student_id:
        return None
    
    # Build payload from progression_data (matches bot.py structure)
    payload = {
        "InId": progression_data.get("InId"),
        "PrID": progression_data.get("PrID"),
        "CrID": progression_data.get("CrID"),
        "DeptID": progression_data.get("DeptID"),
        "SemID": progression_data.get("SemID"),
        "AcYr": progression_data.get("AcYr"),
        "CmProgID": progression_data.get("CmProgID"),
        "StuID": student_id,
        "isFE": True,
        "isForWeb": True,
        "isFrAbLg": True
    }
    
    try:
        response = session.post(ATTENDANCE_DATA_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch attendance data: {e}")
        return None

def fetch_timetable_data(session, progression_data):
    """Fetch today's timetable data"""
    if not progression_data:
        return None
    
    now = get_ist_now()
    today_date = now.strftime("%Y-%m-%d")
    
    payload = progression_data.copy()   
    payload.update({
        "enableV2": True,
        "start": today_date,
        "end": today_date,
        "usrTime": now.strftime("%d-%m-%Y, %I:%M %p"),
        "schdlTyp": "slctdSchdl",
        "isShowCancelledPeriod": True,
        "isFromTt": True
    })
    
    try:
        response = session.post(TIMETABLE_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch timetable data: {e}")
        return None

def format_timetable_summary(timetable_data):
    """Format timetable data into readable summary"""
    if not timetable_data or not timetable_data.get("output", {}).get("data"):
        return "No timetable data available for today"
    
    summary = "Today's Timetable:\n\n"
    
    for day in timetable_data["output"]["data"]:
        periods = day.get("Periods", [])
        if not periods:
            return "No classes scheduled for today"
        
        for idx, period in enumerate(periods, 1):
            # Get subject name
            subject_name = period.get("SubNa", "Unknown Subject")
            
            # Get faculty name
            faculty_name = period.get("StaffNm", "Unknown Faculty")
            
            # Get room/location
            room = period.get("Location", "TBA")
            
            # Get time from start and end fields
            start_time = period.get("start", "")
            end_time = period.get("end", "")
            
            # Format time if available
            time_str = ""
            if start_time and end_time:
                try:
                    # Parse ISO format datetime string (already in IST)
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    
                    # Just extract time without timezone conversion (already IST)
                    start = start_dt.strftime("%I:%M %p")
                    end = end_dt.strftime("%I:%M %p")
                    time_str = f"{start} - {end}"
                except:
                    time_str = f"{start_time} - {end_time}"
            
            summary += f"Period {idx}\n"
            summary += f"{subject_name}\n"
            summary += f"Faculty: {faculty_name}\n"
            summary += f"Room: {room}\n"
            if time_str:
                summary += f"Time: {time_str}\n"
            summary += "\n"
    
    return summary.strip()

def fetch_cafeteria_menu(session, student_id, institution_id):
    """Fetch today's cafeteria menu"""
    if not student_id or not institution_id:
        return None
    
    # Get current day name in 3-letter format
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    today = get_ist_now()
    day_name = days[today.weekday()]
    
    payload = {
        "stuId": student_id,
        "InId": institution_id,
        "day": day_name
    }
    
    try:
        response = session.post(CAFETERIA_MENU_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch cafeteria menu: {e}")
        return None

def format_cafeteria_menu(menu_data):
    """Format cafeteria menu data into readable summary"""
    if not menu_data or not menu_data.get("output", {}).get("data"):
        return "No cafeteria menu available for today"
    
    data = menu_data["output"]["data"]
    meal_list = data.get("oMealList", [])
    
    if not meal_list:
        return "No meals scheduled for today"
    
    summary = "Today's Cafeteria Menu:\n\n"
    facility = data.get("facNme", "Cafeteria")
    summary += f"Location: {facility}\n\n"
    
    for meal in meal_list:
        meal_time = meal.get("mealTm", "")
        meal_items = meal.get("msNme", "")
        
        # Clean up meal name (extract just the time part if available)
        if meal_time:
            summary += f"{meal_time}\n"
        
        # Clean and format menu items
        if meal_items:
            # Split by newlines and clean up
            items = [item.strip() for item in meal_items.split('\n') if item.strip()]
            for item in items:
                if item and item != '-':
                    summary += f"  {item}\n"
        
        summary += "\n"
    
    return summary.strip()

def format_attendance_summary(email, attendance_data):
    """Format attendance data into readable summary"""
    if not attendance_data or not attendance_data.get("output", {}).get("data"):
        return f"{email}: No data available"
    
    data = attendance_data["output"]["data"]
    overall_percentage = data.get("OvrAllPrcntg", 0)
    current_month_percentage = data.get("CurMnthPrcntg", 0)
    overall_present = data.get("OvrAllPCnt", 0)
    overall_total = data.get("OvrAllCnt", 0)
    current_month_present = data.get("CurMPCnt", 0)
    current_month_total = data.get("CurMCnt", 0)
    
    summary = f"Overall Attendance: {overall_percentage}% ({overall_present}/{overall_total})\n"
    summary += f"This Month: {current_month_percentage}% ({current_month_present}/{current_month_total})\n\n"
    
    # Subject-wise breakdown
    subjects = data.get("subjectList", [])
    if subjects:
        summary += "Subject Details:\n\n"
        for subject in subjects:
            subj_code = subject.get("SubjCd", "Unknown")
            subj_name = subject.get("SubjNm", "Unknown")
            attendance_pct = subject.get("OvrAllPrcntg", 0)
            present = subject.get("prsentCnt", 0)
            absent = subject.get("absentCnt", 0)
            leave = subject.get("leaveCnt", 0)
            on_duty = subject.get("onDutyCnt", 0)
            med_leave = subject.get("medLeaveCnt", 0)
            total = subject.get("all", 0)
            
            summary += f"{subj_code}\n"
            summary += f"{subj_name}\n"
            summary += f"Attendance: {attendance_pct}% ({present}/{total})\n"
            summary += f"Present: {present}, Absent: {absent}"
            
            # Add optional fields if they have values
            if leave > 0:
                summary += f", Leave: {leave}"
            if on_duty > 0:
                summary += f", On Duty: {on_duty}"
            if med_leave > 0:
                summary += f", Medical Leave: {med_leave}"
            
            summary += f"\n\n"
    
    return summary

def run_report():
    """Execute the daily report"""
    print("\nDaily Attendance Data Fetcher")
    print(f"Run Date: {get_ist_now().strftime('%d-%m-%Y %I:%M %p')}\n")
    print("Using environment variables for all credentials")
    print()
    
    # Process user
    email = USER_EMAIL
    password = USER_PASSWORD
    
    print(f"Processing: {email}")
    
    # Login
    session, login_data = login_user(email, password)
    if not session or not login_data:
        print(f"  Failed to login")
        send_telegram_message(f"Daily Attendance Report Failed\n\nEmail: {email}\nError: Login failed")
        return
    
    progression_data, student_id = login_data
    print(f"  Logged in successfully")
    
    # Get institution ID
    institution_id = progression_data.get("InId")
    
    # Fetch attendance data
    attendance_data = fetch_attendance_data(session, progression_data, student_id)
    if not attendance_data:
        print(f"  Failed to fetch attendance data")
        send_telegram_message(f"Daily Attendance Report Failed\n\nEmail: {email}\nError: Failed to fetch data")
        return
    
    print(f"  Attendance data fetched")
    
    # Fetch timetable data
    timetable_data = fetch_timetable_data(session, progression_data)
    if timetable_data:
        print(f"  Timetable data fetched")
    else:
        print(f"  No timetable data available")
    
    # Fetch cafeteria menu
    cafeteria_data = fetch_cafeteria_menu(session, student_id, institution_id)
    if cafeteria_data:
        print(f"  Cafeteria menu fetched")
    else:
        print(f"  No cafeteria menu available")
    
    # Format summaries
    attendance_summary = format_attendance_summary(email, attendance_data)
    timetable_summary = format_timetable_summary(timetable_data) if timetable_data else "No timetable available"
    cafeteria_summary = format_cafeteria_menu(cafeteria_data) if cafeteria_data else "No cafeteria menu available"
    
    # Create header with date, time, and email
    now = get_ist_now()
    date_str = now.strftime('%d-%m-%Y')
    time_str = now.strftime('%I:%M %p')
    header = f"Daily Report\n"
    header += f"Date: {date_str}\n"
    header += f"Time: {time_str}\n"
    header += f"Email: {email}\n"
    
    # Combine all reports (Header -> Timetable -> Attendance -> Menu)
    full_report = f"{header}\n\n{'-' * 40}\n\n{timetable_summary}\n\n{'-' * 40}\n\n{attendance_summary}\n\n{'-' * 40}\n\n{cafeteria_summary}"
    
    # Generate final report
    print("\nDAILY REPORT\n")
    print(full_report)
    
    # Send to Telegram (split if too long)
    if len(full_report) > 4000:
        # Split into chunks
        chunks = []
        current_chunk = full_report[:4000]
        remaining = full_report[4000:]
        chunks.append(current_chunk)
        
        while remaining:
            chunks.append(remaining[:4000])
            remaining = remaining[4000:]
        
        for i, chunk in enumerate(chunks):
            send_telegram_message(f"Part {i+1}/{len(chunks)}:\n\n{chunk}")
    else:
        send_telegram_message(full_report)
    
    print("\nDaily report completed successfully!")

def should_run_today():
    """Check if report should run today based on IST time"""
    now = get_ist_now()
    # Set the time you want the report to run (1:00 AM IST)
    run_hour = 1  # 1 AM
    run_minute = 0
    
    # Check if it's past the run time today and hasn't run yet
    current_hour = now.hour
    current_minute = now.minute
    
    # Store last run time in a file
    last_run_file = "/tmp/last_run_date.txt"
    last_run_date = None
    
    try:
        if os.path.exists(last_run_file):
            with open(last_run_file, 'r') as f:
                last_run_date = f.read().strip()
    except Exception as e:
        print(f"Error reading last run file: {e}")
        last_run_date = None
    
    today_date = now.strftime("%Y-%m-%d")
    
    # If already ran today, don't run again
    if last_run_date == today_date:
        return False
    
    # If it's past the scheduled time, run the report
    if current_hour > run_hour or (current_hour == run_hour and current_minute >= run_minute):
        # Update last run date
        try:
            with open(last_run_file, 'w') as f:
                f.write(today_date)
        except Exception as e:
            print(f"Error writing last run file: {e}")
        return True
    
    return False

def main():
    """Main execution - runs report or waits for scheduled time"""
    # Run immediately on startup (for testing and Railway deployment)
    try:
        run_report()
    except Exception as e:
        print(f"Error running initial report: {e}")
    
    # Then check every hour if it's time to run the scheduled report
    print("\nScheduler active. Next check in 1 hour...")
    
    while True:
        try:
            time.sleep(3600)  # Wait 1 hour
            if should_run_today():
                print("\nScheduled run time reached. Running daily report...")
                run_report()
                print("Scheduler active. Next check in 1 hour...")
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
            break
        except Exception as e:
            print(f"Error in scheduler loop: {e}")
            print("Continuing...")
            continue

if __name__ == "__main__":
    main()
