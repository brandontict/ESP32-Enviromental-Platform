import time
import math
import gc
import network
import socket
import json
import ssl
from machine import Pin, unique_id, reset
from dht import DHT22
import ubinascii

# Configuration
SSID = "SSID HERE"
PASSWORD = "PASSWORD"
DHT22_DATA_PIN = 4

print("🚀 ESP32 DHT22 Complete Environmental Platform")
print("=" * 50)

# Initialize sensor
dht22 = DHT22(Pin(DHT22_DATA_PIN))
print(f"✅ DHT22 initialized on GPIO {DHT22_DATA_PIN}")

# Global data storage with enhanced tracking
class EnvironmentalData:
    def __init__(self):
        self.readings = []
        self.max_readings = 50  # REDUCED: was 200, now 50 to save memory
        self.start_time = time.ticks_ms()
        self.total_requests = 0
        self.last_reading_time = 0
        self.sensor_errors = 0
        self.device_id = ubinascii.hexlify(unique_id()).decode()
        
        # Current values
        self.current_temp = 20.0
        self.current_humidity = 50.0
        self.current_vpd = 1.0
        
        # All-time statistics
        self.all_time_min_temp = 999
        self.all_time_max_temp = -999
        self.all_time_min_humidity = 999
        self.all_time_max_humidity = -999
        self.all_time_min_vpd = 999
        self.all_time_max_vpd = -999
        
        # Session statistics
        self.session_min_temp = 999
        self.session_max_temp = -999
        self.session_min_humidity = 999
        self.session_max_humidity = -999
        self.session_min_vpd = 999
        self.session_max_vpd = -999
        
        # Running averages
        self.avg_temp = 0
        self.avg_humidity = 0
        self.avg_vpd = 0
        
    def add_reading(self, temp, humidity, vpd):
        current_time = time.ticks_ms()
        
        reading = {
            'timestamp': current_time,
            'time_str': self._format_time(current_time),
            'temperature': temp,
            'humidity': humidity,
            'vpd': vpd,
            'temp_f': temp * 9/5 + 32
        }
        
        self.readings.append(reading)
        
        # Keep only recent readings - clean up multiple at once for efficiency
        if len(self.readings) > self.max_readings:
            self.readings = self.readings[-self.max_readings:]
            gc.collect()  # Clean up after trimming
        
        # Update current values
        self.current_temp = temp
        self.current_humidity = humidity
        self.current_vpd = vpd
        self.last_reading_time = current_time
        
        # Update all statistics
        self._update_all_stats(temp, humidity, vpd)
    
    def _format_time(self, timestamp):
        elapsed = (timestamp - self.start_time) // 1000
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _update_all_stats(self, temp, humidity, vpd):
        # All-time records
        self.all_time_min_temp = min(self.all_time_min_temp, temp)
        self.all_time_max_temp = max(self.all_time_max_temp, temp)
        self.all_time_min_humidity = min(self.all_time_min_humidity, humidity)
        self.all_time_max_humidity = max(self.all_time_max_humidity, humidity)
        self.all_time_min_vpd = min(self.all_time_min_vpd, vpd)
        self.all_time_max_vpd = max(self.all_time_max_vpd, vpd)
        
        # Session records (current readings only)
        if self.readings:
            temps = [r['temperature'] for r in self.readings]
            hums = [r['humidity'] for r in self.readings]
            vpds = [r['vpd'] for r in self.readings]
            
            self.session_min_temp = min(temps)
            self.session_max_temp = max(temps)
            self.session_min_humidity = min(hums)
            self.session_max_humidity = max(hums)
            self.session_min_vpd = min(vpds)
            self.session_max_vpd = max(vpds)
            
            # Running averages
            self.avg_temp = sum(temps) / len(temps)
            self.avg_humidity = sum(hums) / len(hums)
            self.avg_vpd = sum(vpds) / len(vpds)
    
    def get_uptime(self):
        return (time.ticks_ms() - self.start_time) // 1000

    def reset_session_stats(self):
        """Reset session statistics"""
        self.session_min_temp = 999
        self.session_max_temp = -999
        self.session_min_humidity = 999
        self.session_max_humidity = -999
        self.session_min_vpd = 999
        self.session_max_vpd = -999

class EmailAlertSystem:
    def __init__(self):
        self.enabled = False
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = ""
        self.password = ""
        self.to_email = ""
        self.last_email_time = 0
        self.cooldown_minutes = 5
        self.test_mode = False
        
    def configure(self, username, password, to_email, enabled=True):
        """Configure email settings"""
        self.username = username
        self.password = password
        self.to_email = to_email
        self.enabled = enabled
        print(f"📧 Email configured: {username} -> {to_email}")
    
    def send_alert(self, alerts, temp, humidity, vpd):
        """Send email alert"""
        if not self.enabled or not self.username:
            return False
            
        current_time = time.ticks_ms()
        
        # Check cooldown period
        if (current_time - self.last_email_time) < (self.cooldown_minutes * 60 * 1000):
            print(f"📧 Email cooldown active ({self.cooldown_minutes} min)")
            return False
        
        try:
            subject = "🚨 ESP32 DHT22 Environmental Alert"
            body = self._create_alert_email(alerts, temp, humidity, vpd)
            
            if self._send_smtp_email(subject, body):
                self.last_email_time = current_time
                print(f"📧 Alert email sent successfully")
                return True
            else:
                print(f"📧 Email send failed")
                return False
                
        except Exception as e:
            print(f"📧 Email error: {e}")
            return False
    
    def send_test_email(self):
        """Send test email"""
        try:
            subject = "✅ ESP32 DHT22 Test Email"
            body = f"""
ESP32 DHT22 Environmental Monitor Test Email

This is a test email to verify your email alert configuration is working correctly.

Device ID: {data.device_id}
Sensor: DHT22 (High Accuracy)
Current Time: {data._format_time(time.ticks_ms())}
Uptime: {data.get_uptime()} seconds

DHT22 Specifications:
- Temperature Accuracy: ±0.5°C
- Humidity Accuracy: ±2% RH
- Temperature Range: -40°C to 80°C
- Humidity Range: 0% to 100% RH

If you received this email, your alert system is configured correctly!

Best regards,
Your ESP32 DHT22 Environmental Monitor
"""
            return self._send_smtp_email(subject, body)
        except Exception as e:
            print(f"📧 Test email error: {e}")
            return False
    
    def _create_alert_email(self, alerts, temp, humidity, vpd):
        """Create formatted alert email"""
        temp_f = temp * 9/5 + 32
        
        body = f"""
🚨 ENVIRONMENTAL ALERT - DHT22 SENSOR 🚨

Your ESP32 environmental monitor has detected {len(alerts)} condition(s) that exceed your configured thresholds.

CURRENT READINGS:
🌡️  Temperature: {temp:.1f}°C ({temp_f:.1f}°F)
💧 Humidity: {humidity:.1f}%
📊 VPD: {vpd:.2f} kPa

ACTIVE ALERTS:
"""
        
        for i, alert in enumerate(alerts, 1):
            severity_emoji = "🔴" if alert.get('severity') == 'high' else "🔵"
            message = str(alert.get('message', 'Unknown alert'))
            body += f"{i}. {severity_emoji} {message}\n"
        
        body += f"""

DEVICE INFORMATION:
Device ID: {data.device_id}
Sensor: DHT22 (±0.5°C, ±2% RH accuracy)
Data Pin: GPIO {DHT22_DATA_PIN}
Uptime: {data.get_uptime() // 3600}h {(data.get_uptime() % 3600) // 60}m
Total Readings: {len(data.readings)}

This alert was sent automatically by your ESP32 DHT22 Environmental Monitor.
Next alert will be sent after {self.cooldown_minutes} minutes cooldown period.

To manage your alerts, visit your ESP32 web interface.
"""
        return body
    
    def _send_smtp_email(self, subject, body):
        """Send email via SMTP"""
        try:
            # Connect to SMTP server
            print(f"📧 Connecting to {self.smtp_server}:{self.smtp_port}")
            s = socket.socket()
            s.settimeout(10)
            s.connect((self.smtp_server, self.smtp_port))
            
            # Read greeting
            response = s.recv(1024)
            print(f"📧 Server: {response[:50]}...")
            
            # Send EHLO
            s.send(b'EHLO esp32\r\n')
            s.recv(1024)
            
            # Start TLS
            s.send(b'STARTTLS\r\n')
            s.recv(1024)
            
            # Wrap with SSL
            s = ssl.wrap_socket(s)
            
            # Send EHLO again
            s.send(b'EHLO esp32\r\n')
            s.recv(1024)
            
            # Login
            s.send(b'AUTH LOGIN\r\n')
            s.recv(1024)
            
            # Send username (base64 encoded)
            username_b64 = ubinascii.b2a_base64(self.username.encode()).decode().strip()
            s.send(username_b64.encode() + b'\r\n')
            s.recv(1024)
            
            # Send password (base64 encoded)
            password_b64 = ubinascii.b2a_base64(self.password.encode()).decode().strip()
            s.send(password_b64.encode() + b'\r\n')
            response = s.recv(1024)
            
            if b'235' not in response:  # Authentication failed
                print(f"📧 Authentication failed")
                s.close()
                return False
            
            # Send email
            s.send(f'MAIL FROM:<{self.username}>\r\n'.encode())
            s.recv(1024)
            
            s.send(f'RCPT TO:<{self.to_email}>\r\n'.encode())
            s.recv(1024)
            
            s.send(b'DATA\r\n')
            s.recv(1024)
            
            # Email content
            email_content = f"""From: ESP32 DHT22 Monitor <{self.username}>
To: {self.to_email}
Subject: {subject}
Content-Type: text/plain; charset=utf-8

{body}
."""
            
            s.send(email_content.encode())
            s.recv(1024)
            
            s.send(b'QUIT\r\n')
            s.recv(1024)
            s.close()
            
            return True
            
        except Exception as e:
            print(f"📧 SMTP error: {e}")
            try:
                s.close()
            except:
                pass
            return False

class AlarmSystem:
    def __init__(self):
        # DHT22 optimized thresholds (better accuracy allows tighter ranges)
        self.temp_min = 20.0
        self.temp_max = 26.0
        self.humidity_min = 40.0
        self.humidity_max = 60.0
        self.vpd_min = 0.5
        self.vpd_max = 1.2
        self.alerts_enabled = True
        self.alert_log = []
        self.max_log_entries = 50  # REDUCED: was 100, now 50 to save memory
        
    def check_alerts(self, temp, humidity, vpd):
        current_time = time.ticks_ms()
        alerts = []
        
        # Temperature alerts
        if temp < self.temp_min:
            alerts.append({
                'type': 'temperature',
                'severity': 'low',
                'message': f"Temperature LOW: {temp:.1f}°C ({temp*9/5+32:.1f}°F) - Min: {self.temp_min}°C",
                'value': temp,
                'threshold': self.temp_min
            })
        elif temp > self.temp_max:
            alerts.append({
                'type': 'temperature', 
                'severity': 'high',
                'message': f"Temperature HIGH: {temp:.1f}°C ({temp*9/5+32:.1f}°F) - Max: {self.temp_max}°C",
                'value': temp,
                'threshold': self.temp_max
            })
        
        # Humidity alerts
        if humidity < self.humidity_min:
            alerts.append({
                'type': 'humidity',
                'severity': 'low', 
                'message': f"Humidity LOW: {humidity:.1f}% - Min: {self.humidity_min}%",
                'value': humidity,
                'threshold': self.humidity_min
            })
        elif humidity > self.humidity_max:
            alerts.append({
                'type': 'humidity',
                'severity': 'high',
                'message': f"Humidity HIGH: {humidity:.1f}% - Max: {self.humidity_max}%", 
                'value': humidity,
                'threshold': self.humidity_max
            })
        
        # VPD alerts
        if vpd < self.vpd_min:
            alerts.append({
                'type': 'vpd',
                'severity': 'low',
                'message': f"VPD LOW: {vpd:.2f}kPa - Min: {self.vpd_min}kPa (Too humid for optimal growth)",
                'value': vpd,
                'threshold': self.vpd_min
            })
        elif vpd > self.vpd_max:
            alerts.append({
                'type': 'vpd',
                'severity': 'high', 
                'message': f"VPD HIGH: {vpd:.2f}kPa - Max: {self.vpd_max}kPa (Too dry, may stress plants)",
                'value': vpd,
                'threshold': self.vpd_max
            })
        
        # Log alerts
        if alerts:
            alert_entry = {
                'timestamp': current_time,
                'time_str': data.readings[-1]['time_str'] if data.readings else "00:00:00",
                'alerts': alerts,
                'temp': temp,
                'humidity': humidity,
                'vpd': vpd
            }
            
            self.alert_log.append(alert_entry)
            
            # Keep only recent alerts - clean up multiple at once
            if len(self.alert_log) > self.max_log_entries:
                self.alert_log = self.alert_log[-self.max_log_entries:]
                gc.collect()
            
            # Send email alert
            if self.alerts_enabled:
                email_system.send_alert(alerts, temp, humidity, vpd)
        
        return alerts

class NetworkMonitor:
    def __init__(self):
        self.start_time = time.ticks_ms()
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        self.request_count = 0
        self.last_request_time = 0
        
    def log_request(self, bytes_sent, bytes_received):
        self.total_bytes_sent += bytes_sent
        self.total_bytes_received += bytes_received
        self.request_count += 1
        self.last_request_time = time.ticks_ms()
    
    def get_uptime(self):
        return (time.ticks_ms() - self.start_time) / 1000
    
    def format_bytes(self, bytes_val):
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val/1024:.1f} KB"
        else:
            return f"{bytes_val/(1024*1024):.1f} MB"

# Initialize global objects
data = EnvironmentalData()
alarms = AlarmSystem()
network_monitor = NetworkMonitor()
email_system = EmailAlertSystem()

def calculate_vpd(temperature, humidity):
    try:
        if temperature is None or humidity is None:
            return 1.0
        svp = 0.6107 * math.exp((17.27 * temperature) / (temperature + 237.3))
        avp = (humidity / 100.0) * svp
        vpd = svp - avp
        return max(0, vpd)
    except:
        return 1.0

def read_sensor():
    try:
        dht22.measure()
        time.sleep(0.1)
        
        temp = dht22.temperature()
        hum = dht22.humidity()
        
        if temp is not None and hum is not None:
            # DHT22 has wider range: -40°C to 80°C, 0% to 100% RH
            if -40 <= temp <= 80 and 0 <= hum <= 100:
                vpd = calculate_vpd(temp, hum)
                data.add_reading(temp, hum, vpd)
                return temp, hum, vpd
        
        data.sensor_errors += 1
        print(f"⚠️ DHT22 reading failed - using last known values")
        return data.current_temp, data.current_humidity, data.current_vpd
        
    except Exception as e:
        print(f"❌ DHT22 error: {e}")
        data.sensor_errors += 1
        return data.current_temp, data.current_humidity, data.current_vpd

def get_vpd_status(vpd):
    if vpd < 0.4:
        return {"status": "Too Low", "color": "#ff6b6b", "advice": "Increase temperature or decrease humidity"}
    elif vpd <= 0.8:
        return {"status": "Ideal", "color": "#51cf66", "advice": "Perfect conditions for most plants"}
    elif vpd <= 1.2:
        return {"status": "Good", "color": "#69db7c", "advice": "Good for vegetative growth"}
    elif vpd <= 1.6:
        return {"status": "Acceptable", "color": "#ffd43b", "advice": "OK for flowering stage"}
    else:
        return {"status": "Too High", "color": "#ff6b6b", "advice": "Decrease temperature or increase humidity"}

def handle_post_request(request_data):
    try:
        if b'POST' in request_data:
            data_str = request_data.decode('utf-8')
            if '\r\n\r\n' in data_str:
                body = data_str.split('\r\n\r\n')[1]
                
                # Parse form data
                params = {}
                for param in body.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value.replace('+', ' ').replace('%40', '@')
                
                # Update alarm settings
                if 'temp_min' in params:
                    alarms.temp_min = float(params['temp_min'])
                if 'temp_max' in params:
                    alarms.temp_max = float(params['temp_max'])
                if 'humidity_min' in params:
                    alarms.humidity_min = float(params['humidity_min'])
                if 'humidity_max' in params:
                    alarms.humidity_max = float(params['humidity_max'])
                if 'vpd_min' in params:
                    alarms.vpd_min = float(params['vpd_min'])
                if 'vpd_max' in params:
                    alarms.vpd_max = float(params['vpd_max'])
                
                # Update email settings
                if 'email_username' in params:
                    email_system.username = params['email_username']
                if 'email_password' in params:
                    email_system.password = params['email_password']
                if 'email_to' in params:
                    email_system.to_email = params['email_to']
                if 'email_enabled' in params:
                    email_system.enabled = params['email_enabled'] == 'on'
                if 'email_cooldown' in params:
                    email_system.cooldown_minutes = int(params['email_cooldown'])
                
                # Handle special actions
                action = params.get('action', '')
                if action == 'clear_logs':
                    alarms.alert_log.clear()
                    print("Alert logs cleared")
                elif action == 'reset_stats':
                    data.reset_session_stats()
                    print("Session statistics reset")
                elif action == 'test_email':
                    if email_system.send_test_email():
                        print("✅ Test email sent successfully")
                    else:
                        print("❌ Test email failed")
                elif action == 'restart':
                    print("Restarting ESP32...")
                    time.sleep(1)
                    reset()
                
                print("Settings updated via web interface")
                
    except Exception as e:
        print(f"⚠️ POST processing error: {e}")

def create_simple_web_page(temp, hum, vpd, current_alerts):
    """Create a minimal, fast-loading HTML response"""
    
    temp_f = temp * 9.0/5.0 + 32
    vpd_info = get_vpd_status(vpd)
    uptime = data.get_uptime()
    
    # Alert status
    alert_text = f"ALERT: {len(current_alerts)} active" if current_alerts else "All systems normal"
    alert_style = "background:#f8d7da;color:#721c24" if current_alerts else "background:#d4edda;color:#155724"
    
    # Email status
    email_status = "ON" if email_system.enabled and email_system.username else "OFF"
    
    # Build minimal alerts (keep very short)
    alerts_html = ""
    if current_alerts:
        for alert in current_alerts[:2]:  # Only show 2 max
            try:
                alert_type = str(alert.get('type', ''))[:4].upper()  # Just first 4 chars
                alerts_html += f'<div>{alert_type}: {str(alert.get("message", ""))[:40]}...</div>'
            except:
                alerts_html += '<div>ALERT: Display error</div>'
    
    # Build alerts section separately to avoid nested f-string issues
    alerts_section = ""
    if alerts_html:
        alerts_section = f'<div class="alerts"><strong>Active Alerts:</strong><br>{alerts_html}</div>'
    
    # MINIMAL HTML - much smaller and faster
    html = f'''<!DOCTYPE html>
<html><head>
    <title>ESP32 DHT22</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <style>
        body{{font-family:Arial;margin:0;background:#f5f5f5;}}
        .header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;text-align:center;}}
        .container{{max-width:800px;margin:0 auto;padding:20px;}}
        .alert{{padding:10px;margin:10px 0;border-radius:5px;font-weight:bold;text-align:center;}}
        .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:20px 0;}}
        .card{{background:white;border-radius:8px;padding:15px;box-shadow:0 2px 4px rgba(0,0,0,0.1);}}
        .temp{{border-left:4px solid #dc3545;}}
        .humidity{{border-left:4px solid #28a745;}}
        .vpd{{border-left:4px solid #6f42c1;}}
        .value{{font-size:2em;font-weight:bold;margin:5px 0;}}
        .subtitle{{color:#666;font-size:0.9em;}}
        .config{{background:white;border-radius:8px;padding:15px;margin:15px 0;}}
        .form-row{{display:flex;gap:10px;margin:10px 0;flex-wrap:wrap;}}
        .form-group{{flex:1;min-width:120px;}}
        .form-group input{{width:100%;padding:5px;border:1px solid #ddd;border-radius:3px;}}
        .btn{{background:#007bff;color:white;border:none;padding:8px 15px;border-radius:3px;margin:3px;cursor:pointer;}}
        .btn-warn{{background:#ffc107;color:#212529;}}
        .btn-danger{{background:#dc3545;}}
        .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(80px,1fr));gap:8px;margin:10px 0;}}
        .stat{{text-align:center;padding:8px;background:#f8f9fa;border-radius:3px;}}
        .stat-val{{font-size:1.1em;font-weight:bold;}}
        .stat-label{{color:#666;font-size:0.8em;}}
        .vpd-status{{padding:8px;border-radius:3px;margin:5px 0;text-align:center;font-weight:bold;color:white;}}
        .alerts{{background:#fff3cd;border-radius:3px;padding:10px;margin:10px 0;}}
        @media (max-width:600px){{.cards{{grid-template-columns:1fr;}}.form-row{{flex-direction:column;}}}}
    </style>
</head>
<body>
    <div class="header">
        <h1>ESP32 DHT22 Monitor</h1>
        <p>DHT22 Environmental Sensor</p>
    </div>
    
    <div class="container">
        <div class="alert" style="{alert_style}">{alert_text}</div>
        
        <div class="cards">
            <div class="card temp">
                <h3>TEMPERATURE</h3>
                <div class="value">{temp:.1f}°C</div>
                <div class="subtitle">{temp_f:.1f}°F</div>
                <div class="subtitle">Range: {data.session_min_temp:.1f} - {data.session_max_temp:.1f}°C</div>
            </div>
            
            <div class="card humidity">
                <h3>HUMIDITY</h3>
                <div class="value">{hum:.1f}%</div>
                <div class="subtitle">Relative Humidity</div>
                <div class="subtitle">Range: {data.session_min_humidity:.1f} - {data.session_max_humidity:.1f}%</div>
            </div>
            
            <div class="card vpd">
                <h3>VPD</h3>
                <div class="value">{vpd:.2f} kPa</div>
                <div class="vpd-status" style="background-color:{vpd_info['color']};">{vpd_info['status']}</div>
            </div>
        </div>
        
        {alerts_section}
        
        <div class="config">
            <h3>Quick Config</h3>
            <form method="post">
                <div class="form-row">
                    <div class="form-group">
                        <label>Temp Min:</label>
                        <input type="number" name="temp_min" value="{alarms.temp_min}" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Temp Max:</label>
                        <input type="number" name="temp_max" value="{alarms.temp_max}" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Hum Min:</label>
                        <input type="number" name="humidity_min" value="{alarms.humidity_min}">
                    </div>
                    <div class="form-group">
                        <label>Hum Max:</label>
                        <input type="number" name="humidity_max" value="{alarms.humidity_max}">
                    </div>
                </div>
                <button type="submit" class="btn">Update</button>
            </form>
            
            <h4>Email: {email_status}</h4>
            <form method="post">
                <div class="form-row">
                    <div class="form-group">
                        <input type="email" name="email_username" value="{email_system.username}" placeholder="Gmail">
                    </div>
                    <div class="form-group">
                        <input type="password" name="email_password" placeholder="App Password">
                    </div>
                    <div class="form-group">
                        <input type="email" name="email_to" value="{email_system.to_email}" placeholder="Send to">
                    </div>
                </div>
                <button type="submit" class="btn">Save</button>
                <button type="submit" name="action" value="test_email" class="btn btn-warn">Test</button>
            </form>
            
            <div style="margin:10px 0;">
                <button type="button" onclick="location.reload()" class="btn">Refresh</button>
                <form method="post" style="display:inline;">
                    <button type="submit" name="action" value="restart" class="btn btn-danger" onclick="return confirm('Restart?')">Restart</button>
                </form>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-val">{len(data.readings)}</div>
                <div class="stat-label">Readings</div>
            </div>
            <div class="stat">
                <div class="stat-val">{data.sensor_errors}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat">
                <div class="stat-val">{round(uptime/3600, 1)}h</div>
                <div class="stat-label">Uptime</div>
            </div>
            <div class="stat">
                <div class="stat-val">{gc.mem_free()}</div>
                <div class="stat-label">Free RAM</div>
            </div>
            <div class="stat">
                <div class="stat-val">{round(data.avg_temp, 1)}°C</div>
                <div class="stat-label">Avg Temp</div>
            </div>
        </div>
        
        <div style="background:#e3f2fd;padding:10px;border-radius:5px;font-size:0.9em;">
            <strong>Device:</strong> {data.device_id[:8]}... | 
            <strong>Sensor:</strong> DHT22 GPIO{DHT22_DATA_PIN} | 
            <strong>Email:</strong> {email_status}
        </div>
    </div>
</body>
</html>'''
    
    return html

def send_web_page_streaming(client_socket, temp, hum, vpd, current_alerts):
    """Send HTML page in fewer, larger chunks to avoid connection issues"""
    
    def send_chunk(html_chunk):
        try:
            # Check if socket is still connected before sending
            client_socket.settimeout(5)  # 5 second timeout
            client_socket.sendall(html_chunk.encode())
            gc.collect()  # Clean up after each chunk
            return True
        except Exception as e:
            print(f"⚠️ Connection lost: {e}")
            return False
    
    temp_f = temp * 9.0/5.0 + 32
    vpd_info = get_vpd_status(vpd)
    uptime = data.get_uptime()
    
    # Alert status
    alert_class = "alert-danger" if current_alerts else "alert-success"
    alert_text = f"🚨 {len(current_alerts)} ACTIVE ALERTS" if current_alerts else "✅ ALL SYSTEMS NORMAL"
    
    # Email status
    email_status = "✅ Enabled" if email_system.enabled and email_system.username else "❌ Disabled"
    
    # Send HTTP headers first
    headers = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
    client_socket.send(headers.encode())
    
    # HTML Head and CSS (simplified but still attractive)
    send_chunk('''<!DOCTYPE html>
<html><head>
    <title>ESP32 DHT22 Environmental Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <style>
        * { box-sizing: border-box; }
        body { font-family: Arial; margin: 0; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
        .sensor-badge { background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; display: inline-block; margin-top: 10px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .alert-banner { padding: 15px; margin: 20px 0; border-radius: 8px; font-weight: bold; text-align: center; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 20px 0; }
        .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #007bff; }
        .card.temp { border-left-color: #dc3545; }
        .card.humidity { border-left-color: #28a745; }
        .card.vpd { border-left-color: #6f42c1; }
        .card-value { font-size: 2.5em; font-weight: bold; margin: 10px 0; }
        .card-subtitle { color: #666; font-size: 1.1em; }
        .min-max { font-size: 0.9em; color: #888; margin: 5px 0; }
        .accuracy-badge { background: #e8f5e8; color: #2e7d32; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; margin: 5px 0; display: inline-block; }
        .vpd-status { padding: 10px; border-radius: 5px; margin: 10px 0; text-align: center; font-weight: bold; }
        .config-section { background: white; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { font-weight: bold; margin-bottom: 5px; }
        .form-group input, .form-group select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn-danger { background: #dc3545; }
        .btn-success { background: #28a745; }
        .btn-warning { background: #ffc107; color: #212529; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .stat-item { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }
        .stat-value { font-size: 1.5em; font-weight: bold; color: #333; }
        .stat-label { color: #666; font-size: 0.9em; margin-top: 5px; }
        .logs-section { background: white; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-height: 400px; overflow-y: auto; }
        .log-entry { background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #dc3545; }
        .system-info { background: #e3f2fd; border-radius: 10px; padding: 20px; margin: 20px 0; }
        .info-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #ddd; }
        .tabs { display: flex; background: #f8f9fa; border-radius: 8px; margin-bottom: 20px; }
        .tab { flex: 1; padding: 12px; background: none; border: none; cursor: pointer; border-radius: 8px; font-weight: bold; }
        .tab.active { background: #007bff; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        @media (max-width: 768px) { .dashboard { grid-template-columns: 1fr; } }
    </style>
</head><body>''')
    
    # Header
    send_chunk(f'''
    <div class="header">
        <h1>🌡️ ESP32 DHT22 Environmental Monitor Pro</h1>
        <p>DHT22 Sensor • High Accuracy Environmental Control • Email Alerts</p>
        <div class="sensor-badge">📡 DHT22: ±0.5°C, ±2% RH Accuracy</div>
    </div>
    <div class="container">
        <div class="alert-banner {alert_class}">{alert_text}</div>''')
    
    # Main dashboard
    send_chunk(f'''
        <div class="dashboard">
            <div class="card temp">
                <h3>🌡️ Temperature</h3>
                <div class="card-value">{temp:.1f}°C</div>
                <div class="card-subtitle">{temp_f:.1f}°F</div>
                <div class="accuracy-badge">±0.5°C Accuracy</div>
                <div class="min-max">📈 Session High: {data.session_max_temp:.1f}°C</div>
                <div class="min-max">📉 Session Low: {data.session_min_temp:.1f}°C</div>
                <div class="min-max">🏆 All-Time High: {data.all_time_max_temp:.1f}°C</div>
                <div class="min-max">🥶 All-Time Low: {data.all_time_min_temp:.1f}°C</div>
            </div>
            
            <div class="card humidity">
                <h3>💧 Humidity</h3>
                <div class="card-value">{hum:.1f}%</div>
                <div class="card-subtitle">Relative Humidity</div>
                <div class="accuracy-badge">±2% RH Accuracy</div>
                <div class="min-max">📈 Session High: {data.session_max_humidity:.1f}%</div>
                <div class="min-max">📉 Session Low: {data.session_min_humidity:.1f}%</div>
                <div class="min-max">🏆 All-Time High: {data.all_time_max_humidity:.1f}%</div>
                <div class="min-max">🥶 All-Time Low: {data.all_time_min_humidity:.1f}%</div>
            </div>
            
            <div class="card vpd">
                <h3>📊 VPD</h3>
                <div class="card-value">{vpd:.2f} kPa</div>
                <div class="vpd-status" style="background-color: {vpd_info['color']}; color: white;">
                    {vpd_info['status']}
                </div>
                <div class="card-subtitle">{vpd_info['advice']}</div>
                <div class="min-max">📈 Session High: {data.session_max_vpd:.2f} kPa</div>
                <div class="min-max">📉 Session Low: {data.session_min_vpd:.2f} kPa</div>
            </div>
        </div>''')
    
    # Current alerts if any
    if current_alerts:
        send_chunk('<div class="logs-section"><h3>🚨 Current Alerts</h3>')
        for alert in current_alerts[:5]:  # Limit to 5 alerts max for memory
            try:
                severity_color = "#dc3545" if alert.get('severity') == 'high' else "#ffc107"
                alert_type = str(alert.get('type', 'Unknown')).title()
                alert_message = str(alert.get('message', 'No message'))[:100]  # Truncate long messages
                send_chunk(f'<div class="log-entry" style="border-left-color: {severity_color};"><strong>{alert_type}:</strong> {alert_message}</div>')
            except:
                send_chunk('<div class="log-entry" style="border-left-color: #dc3545;"><strong>Alert Error:</strong> Unable to display alert</div>')
        send_chunk('</div>')
    
    # Configuration section with tabs
    send_chunk(f'''
        <div class="config-section">
            <div class="tabs">
                <button class="tab active" onclick="showTab(event, 'alarms')">🚨 Alarms</button>
                <button class="tab" onclick="showTab(event, 'email')">📧 Email</button>
                <button class="tab" onclick="showTab(event, 'system')">⚙️ System</button>
            </div>
            
            <div id="alarms" class="tab-content active">
                <h3>⚙️ DHT22 Threshold Configuration</h3>
                <form method="post">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Temperature Min (°C):</label>
                            <input type="number" name="temp_min" value="{alarms.temp_min}" step="0.1">
                        </div>
                        <div class="form-group">
                            <label>Temperature Max (°C):</label>
                            <input type="number" name="temp_max" value="{alarms.temp_max}" step="0.1">
                        </div>
                        <div class="form-group">
                            <label>Humidity Min (%):</label>
                            <input type="number" name="humidity_min" value="{alarms.humidity_min}" step="1">
                        </div>
                        <div class="form-group">
                            <label>Humidity Max (%):</label>
                            <input type="number" name="humidity_max" value="{alarms.humidity_max}" step="1">
                        </div>
                        <div class="form-group">
                            <label>VPD Min (kPa):</label>
                            <input type="number" name="vpd_min" value="{alarms.vpd_min}" step="0.01">
                        </div>
                        <div class="form-group">
                            <label>VPD Max (kPa):</label>
                            <input type="number" name="vpd_max" value="{alarms.vpd_max}" step="0.01">
                        </div>
                    </div>
                    <button type="submit" class="btn">Update Alarm Thresholds</button>
                </form>
            </div>''')
    
    # Email tab
    send_chunk(f'''
            <div id="email" class="tab-content">
                <h3>📧 Email Alert Configuration</h3>
                <p style="background: {"#d4edda" if email_system.enabled and email_system.username else "#f8d7da"}; 
                          color: {"#155724" if email_system.enabled and email_system.username else "#721c24"}; 
                          padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">
                    {email_status}
                </p>
                <form method="post">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Gmail Username:</label>
                            <input type="email" name="email_username" value="{email_system.username}" placeholder="your.email@gmail.com">
                        </div>
                        <div class="form-group">
                            <label>Gmail App Password:</label>
                            <input type="password" name="email_password" value="{'*' * len(email_system.password) if email_system.password else ''}" placeholder="App Password">
                        </div>
                        <div class="form-group">
                            <label>Alert Recipient:</label>
                            <input type="email" name="email_to" value="{email_system.to_email}" placeholder="recipient@example.com">
                        </div>
                        <div class="form-group">
                            <label>Cooldown (minutes):</label>
                            <input type="number" name="email_cooldown" value="{email_system.cooldown_minutes}" min="1" max="60">
                        </div>
                        <div class="form-group">
                            <label>Enable Email Alerts:</label>
                            <select name="email_enabled">
                                <option value="on"{'selected' if email_system.enabled else ''}>Enabled</option>
                                <option value="off"{'' if email_system.enabled else 'selected'}>Disabled</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn">Save Email Settings</button>
                    <button type="submit" name="action" value="test_email" class="btn btn-warning">📧 Send Test Email</button>
                </form>
            </div>''')
    
    # System tab
    send_chunk('''
            <div id="system" class="tab-content">
                <h3>⚙️ System Management</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0;">
                    <form method="post" style="display: inline;">
                        <button type="submit" name="action" value="clear_logs" class="btn btn-warning">🗑️ Clear Alert Logs</button>
                    </form>
                    <form method="post" style="display: inline;">
                        <button type="submit" name="action" value="reset_stats" class="btn btn-warning">📊 Reset Statistics</button>
                    </form>
                    <form method="post" style="display: inline;">
                        <button type="submit" name="action" value="restart" class="btn btn-danger" onclick="return confirm('Restart ESP32?')">🔄 Restart Device</button>
                    </form>
                </div>
            </div>
        </div>''')
    
    # Alert logs (if any - keep it small for memory)
    if alarms.alert_log:
        send_chunk(f'<div class="logs-section"><h3>📋 Recent Alert History ({len(alarms.alert_log)} total)</h3>')
        for log_entry in alarms.alert_log[-10:]:  # Show only last 10 entries
            try:
                time_str = str(log_entry.get('time_str', 'Unknown time'))
                alerts_in_entry = log_entry.get('alerts', [])
                if alerts_in_entry:
                    first_alert = alerts_in_entry[0]
                    alert_message = str(first_alert.get('message', 'No message'))[:80]  # Truncate for memory
                    send_chunk(f'<div class="log-entry"><strong>{time_str}:</strong> {alert_message}{"..." if len(str(first_alert.get('message', ''))) > 80 else ""}</div>')
            except:
                send_chunk('<div class="log-entry">Error displaying log entry</div>')
        send_chunk('</div>')
    
    # System statistics
    send_chunk(f'''<div class="system-info">
            <h3>🔧 DHT22 System Information & Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{len(data.readings)}</div>
                    <div class="stat-label">Data Points</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{data.sensor_errors}</div>
                    <div class="stat-label">Sensor Errors</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{network_monitor.request_count}</div>
                    <div class="stat-label">Total Requests</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{round(uptime/3600, 1)}h</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{network_monitor.format_bytes(gc.mem_free())}</div>
                    <div class="stat-label">Free Memory</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{round(data.avg_temp, 1)}°C</div>
                    <div class="stat-label">Avg Temperature</div>
                </div>
            </div>''')
    
    # Device information rows
    send_chunk(f'''
            <div class="info-row">
                <span>Device ID:</span>
                <span>{data.device_id}</span>
            </div>
            <div class="info-row">
                <span>Sensor:</span>
                <span>DHT22 on GPIO {DHT22_DATA_PIN} (±0.5°C, ±2% RH)</span>
            </div>
            <div class="info-row">
                <span>Temperature Range:</span>
                <span>-40°C to 80°C (-40°F to 176°F)</span>
            </div>
            <div class="info-row">
                <span>Last Reading:</span>
                <span>{(time.ticks_ms() - data.last_reading_time) // 1000} seconds ago</span>
            </div>
            <div class="info-row">
                <span>Email Alerts:</span>
                <span>{email_status}</span>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(evt, tabName) {{
            var i, tabcontent, tabs;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].classList.remove("active");
            }}
            tabs = document.getElementsByClassName("tab");
            for (i = 0; i < tabs.length; i++) {{
                tabs[i].classList.remove("active");
            }}
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
        }}
    </script>
</body></html>''')
    
    print(f"✅ Streamed webpage successfully | Free memory: {gc.mem_free()} bytes")

def connect_wifi():
    print(f"🌐 Connecting to WiFi: {SSID}")
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    
    if wlan.isconnected():
        print("✅ Already connected!")
        return wlan.ifconfig()[0]
    
    wlan.connect(SSID, PASSWORD)
    
    timeout = 20
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        print(".", end="")
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\n✅ WiFi connected! IP: {ip}")
        return ip
    else:
        print(f"\n❌ WiFi connection failed")
        return None

def main():
    # Initialize with safe default values
    data.current_temp = 20.0
    data.current_humidity = 50.0
    data.current_vpd = 1.0
    data.all_time_min_temp = 20.0
    data.all_time_max_temp = 20.0
    data.all_time_min_humidity = 50.0
    data.all_time_max_humidity = 50.0
    data.all_time_min_vpd = 1.0
    data.all_time_max_vpd = 1.0
    data.session_min_temp = 20.0
    data.session_max_temp = 20.0
    data.session_min_humidity = 50.0
    data.session_max_humidity = 50.0
    data.session_min_vpd = 1.0
    data.session_max_vpd = 1.0
    
    # Test sensor first
    print("Testing DHT22 sensor...")
    try:
        temp, hum, vpd = read_sensor()
        print(f"✅ Test reading: {temp}°C, {hum}%, {vpd:.2f}kPa")
    except Exception as e:
        print(f"⚠️ Sensor test warning: {e}")
        print("Continuing with default values...")
    
    # Connect to WiFi
    ip = connect_wifi()
    if ip is None:
        print("❌ Cannot start without WiFi")
        return
    
    # Start web server
    print("🌐 Starting memory-optimized DHT22 web server...")
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        
        print("✅ Memory-optimized web server started!")
        print("=" * 60)
        print(f"🌐 Access your DHT22 Environmental Monitor at:")
        print(f"   http://{ip}")
        print("🧠 Memory Optimizations:")
        print("   • Streaming HTML generation")
        print("   • Reduced data storage (50 readings vs 200)")
        print("   • Aggressive garbage collection")
        print("   • Chunked response sending")
        print("   • Simplified interface (no heavy charts)")
        print("📡 DHT22 Features:")
        print("   • High accuracy monitoring (±0.5°C, ±2% RH)")
        print("   • Email alerts with Gmail integration")
        print("   • All-time and session statistics")
        print("   • Mobile-responsive interface")
        print("=" * 60)
        
        while True:
            try:
                cl, addr = s.accept()
                
                # Read request
                request = cl.recv(1024)
                request_size = len(request)
                
                # Aggressive memory cleanup before processing
                gc.collect()
                print(f"🧠 Free memory before request: {gc.mem_free()} bytes")
                
                # Handle POST requests
                try:
                    handle_post_request(request)
                except Exception as e:
                    print(f"⚠️ POST processing error: {e}")
                
                # Read sensor
                try:
                    temp, hum, vpd = read_sensor()
                    
                    # Ensure we have valid values
                    if temp is None or hum is None or vpd is None:
                        temp, hum, vpd = 20.0, 50.0, 1.0  # Safe defaults
                        print("Using default values due to sensor issues")
                        
                except Exception as e:
                    print(f"⚠️ Sensor read error: {e}")
                    temp, hum, vpd = 20.0, 50.0, 1.0  # Safe defaults
                
                # Check for alerts
                try:
                    current_alerts = alarms.check_alerts(temp, hum, vpd)
                except Exception as e:
                    print(f"⚠️ Alert check error: {e}")
                    current_alerts = []
                
                # Send response using streaming method
                try:
                    response = create_simple_web_page(temp, hum, vpd, current_alerts)
                    # FIXED: Added proper UTF-8 encoding headers
                    headers = 'HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n'
                    cl.send(headers.encode('utf-8'))
                    cl.sendall(response.encode('utf-8'))
                    cl.close()
                    response_size = len(response)
                except Exception as e:
                    print(f"⚠️ Streaming page error: {e}")
                    try:
                        # Ultra-minimal fallback
                        fallback = f'''HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                        <html><head><title>ESP32 DHT22</title><meta http-equiv="refresh" content="30"></head>
                        <body style="font-family:Arial;padding:20px;">
                        <h1>🌡️ ESP32 DHT22 Monitor</h1>
                        <h2>📊 Current Readings</h2>
                        <p><strong>Temperature:</strong> {temp:.1f}°C ({temp*9/5+32:.1f}°F)</p>
                        <p><strong>Humidity:</strong> {hum:.1f}%</p>
                        <p><strong>VPD:</strong> {vpd:.2f} kPa</p>
                        <p><strong>Free Memory:</strong> {gc.mem_free()} bytes</p>
                        <p>⚠️ Using fallback interface due to memory constraints</p>
                        </body></html>'''
                        cl.send(fallback.encode())
                        cl.close()
                        response_size = len(fallback)
                    except:
                        try:
                            cl.close()
                        except:
                            pass
                
                # Update network statistics
                network_monitor.log_request(response_size, request_size)
                
                # Log activity with email status
                alert_info = f" | 🚨 {len(current_alerts)} alerts" if current_alerts else ""
                email_info = " | 📧 Email: ON" if email_system.enabled and email_system.username else " | 📧 Email: OFF"
                memory_info = f" | 🧠 {gc.mem_free()}B free"
                print(f"📊 #{network_monitor.request_count} | {addr[0]} | {temp:.1f}°C {hum:.1f}% {vpd:.2f}kPa{alert_info}{email_info}{memory_info}")
                
                # Final cleanup
                gc.collect()
                
            except Exception as e:
                print(f"❌ Request error: {e}")
                try:
                    cl.close()
                except:
                    pass
                
    except Exception as e:
        print(f"💥 Server error: {e}")

# Run the complete platform
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 DHT22 Environmental Monitor stopped")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        print("Try restarting the ESP32")
