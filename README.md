# CUhackit-Project

🏀 CourtFlow: Gym & Basketball Court Management System
CourtFlow is a real-time web application designed for gym administrators to monitor basketball court occupancy and for athletes to check in/out seamlessly using dynamic QR codes.

🚀 Key Features
Real-time Occupancy Tracking: A live dashboard for gym staff to see how many players are on each court.

QR-Based Check-in/out: Athletes scan a stationary or digital QR code to start/end their session.

Profile Syncing: User data, membership status, and play history are synced instantly via a cloud-hosted PostgreSQL database.

Capacity Alerts: Automatically flags courts as "Full" when the player count hits the predefined limit.

Ghost Session Management: Automated logic to close sessions for players who forget to check out.

🛠 Tech Stack
Component	Technology	Reason
Frontend	Next.js 14/15	React framework with Server Components for SEO and speed.
Styling	Tailwind CSS	Rapid UI development with a utility-first approach.
Backend/DB	Supabase	Managed PostgreSQL with built-in Auth and Real-time listeners.
QR Logic	qrcode.react / html5-qrcode	Client-side generation and camera-based scanning.
Icons	Lucide React	Clean, lightweight icon set.
📊 Database Schema (Draft)
The system relies on a relational structure to ensure data integrity and real-time updates.

profiles: User identities, roles (Athlete/Admin), and unique QR tokens.

courts: Names, locations, and max_capacity integers.

sessions: Junction table tracking user_id, court_id, check_in_at, and check_out_at.

⚙️ Getting Started
1. Clone the repository

Bash
git clone https://github.com/your-username/courtflow.git
cd courtflow
2. Install dependencies

Bash
npm install
3. Environment Setup

Create a .env.local file in the root directory and add your Supabase credentials:

Code snippet
NEXT_PUBLIC_SUPABASE_URL=your_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
4. Run the development server

Bash
npm run dev
Open http://localhost:3000 to see the result.

🛡 Security & Evidence-Based Practices
To ensure this system is "production-ready," we implement the following:

Row Level Security (RLS): We use PostgreSQL RLS to ensure athletes can only write to their own sessions and cannot modify other users' check-ins.

UUID vs. Sequential IDs: We use UUIDs for qr_code_tokens. According to OWASP security standards, using non-enumerable identifiers prevents "Insecure Direct Object Reference" (IDOR) attacks, where a user could guess another user's check-in ID by simply incrementing a number.

Debounced Scanning: The scanner interface uses a debounce function to prevent multiple check-in API calls from a single QR scan, a common bottleneck in camera-based web apps.

🗺 Roadmap
[ ] Initial Database Schema Setup in Supabase.

[ ] User Authentication (Email/Password & Magic Link).

[ ] QR Code Generation Component.

[ ] Real-time Admin Dashboard for Court Monitoring.

[ ] Automated "Auto-Checkout" Cron Job.