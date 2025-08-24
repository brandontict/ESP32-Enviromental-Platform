 Environmental monitoring via DHT22 sensor sending Tempature and Humiditity values to a local html server . This python script is for a ESP32 device already running MicroPython. 

Joint effort between Claude and I. 

Prerequisites: Micropython installed on ESP32
               DHT22 sensor connected to GPIO 4  

*Installation: Use Thonny or webrepl upload the code as " main.py " inside the root folder. 

Coming Soon: 
Built in VPN / Tunnel 

Features: 

Dashboard Tab:
<p>
🌡️ Temperature - Live readings with status indicators
💧 Humidity - Real-time data with range checking
🌫️ VPD - Calculated vapor pressure deficit
📊 Status Bar - Connection, uptime, reading count
</p>
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


<b>version 3</b>
<img width="1465" height="794" alt="image" src="https://github.com/user-attachments/assets/05e25fa7-8435-4521-a1ab-8dfab2e42aed" />
<img width="1259" height="460" alt="image" src="https://github.com/user-attachments/assets/4191cb0c-7b68-485b-8e5a-01ef138b054f" />
<img width="1270" height="593" alt="image" src="https://github.com/user-attachments/assets/a144a8c2-c5b7-4f31-b79f-0950358fead9" />
<img width="1286" height="647" alt="image" src="https://github.com/user-attachments/assets/df6cd405-adc8-43f0-9df1-f65fbb2c6acb" />


