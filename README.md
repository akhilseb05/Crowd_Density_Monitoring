# Crowd Monitoring System for Festivals
**Real-Time Geospatial Safety & Alerting System**

This project is a high-performance safety solution for managing large-scale public gatherings. It combines a **Django/PostGIS** backend with an **Android-based GPS tracker** to monitor crowd density and trigger automated safety alerts in real-time.

---

## Design & UI (Figma)
The user interface of admin side and attendee registration are created using figma, and the links of them are provided.
* **[Admin Side Prototype](https://www.figma.com/design/ZCk6P6zzFQ9AN81zicw5e2/Crowd-Monitoring?node-id=0-1&t=QbpRbps1QhNrIn59-1)**
*  **[Attendee Side Prototype](https://www.figma.com/design/uwGTtUjbeBdfcmTBUkobzJ/Untitled?t=QbpRbps1QhNrIn59-1)**
---

## Key Features
* **Live GPS Tracking**: Real-time attendee location updates every 15 seconds.
* **Automatic Alert Triggering**: Backend logic calculates density within specific zones and triggers alerts if numbers exceed safe thresholds.
* **Geospatial Fencing**: Define event boundaries and "danger zones" using PostGIS polygon data.
* **Admin Control Center**: A secure web dashboard to manage events, zones, and live data.

---

## Tech Stack
* **Backend**: Python 3.x, Django 5.x, PostgreSQL/PostGIS.
* **Mobile**: Java, Android SDK, Android Studio.
* **Design**: Figma (UI/UX).
* **Networking**: Ngrok for secure HTTPS tunneling (only used in development phase and testing).

---
