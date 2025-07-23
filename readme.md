Full environmental monitoring via DHT22 sensors sending values to a local html server . This python script is for ESP32 device running MicroPython. 

Features: 

Dashboard Tab:

🌡️ Temperature - Live readings with status indicators
💧 Humidity - Real-time data with range checking
🌫️ VPD - Calculated vapor pressure deficit
📊 Status Bar - Connection, uptime, reading count

System Tab:

⚙️ ESP32 Health - Memory usage, CPU frequency
📈 Performance Stats - Total readings, error rates
🔧 Real-time Monitoring - Live system metrics

Alarms Tab:

🚨 Active Alerts - Shows current alarm conditions
⚙️ Threshold Settings - Configure min/max values
💾 Save Settings - Updates stored on ESP32

💡 Memory Usage:

Before: ~45KB (too big!)
After: ~12KB (perfect fit!)
Free RAM: Should show ~100-150KB available

🎯 Key Features:
Smart Alarms:

Temperature range checking
Humidity monitoring
VPD calculation and alerts
Visual status indicators (Good/Warning/Danger)

Live Interface:

Auto-updates every 5 seconds
Connection status monitoring
Responsive design for any device
Beautiful gradient styling

System Monitoring:

Real ESP32 memory usage
CPU frequency display
Uptime tracking
Error rate monitoring

🚀 New Email Features Added:
📧 Email Tab:

Enable/Disable Toggle - Turn email alerts on/off
SMTP Configuration - Server, port, credentials setup
*Alert Settings - Recipient email and cooldown timer
Test Email Function - Verify your settings work

🚨 Smart Email Alerts:

Automatic Sending - Emails sent when alarms trigger
Cooldown Protection - Prevents email spam (5-minute default)
Compact Messages - Optimized for ESP32 memory
SSL/TLS Support - Secure email delivery

⚙️ Gmail Setup Instructions:
1. Enable 2-Factor Authentication:

Go to your Google Account settings
Security → 2-Step Verification → Turn On

2. Generate App Password:

Google Account → Security → App passwords
Select "Mail" and generate password
Use this password, NOT your regular Gmail password!


Joint effort between Claude and I. 

Pre: Have Micropython installed*
     DHT22 sensor connected *

*Installation: Using Thonny or webrepl upload the python code as " main.py " . 

<b>version 3</b>
