Here is the comprehensive, step-by-step blueprint for building, automating, and launching your platform. This plan is broken down into distinct phases, from infrastructure to AI integration, structured as an actionable checklist.

## Phase 1: Project Identity & Methodology Foundation

Before writing a single line of code, the rules of the data must be established. This ensures the site remains credible and focused on its human-centric mission.

- [ ] **Draft the Core Anchor Statement:** Write out the exact phrasing of your "Better Nigeria" definition: _"A Nigeria where a sizable number of people can say that their today was better than their yesterday..."_ Decide where this will live permanently on the UI (e.g., a sticky footer or the hero section header).
    
- [ ] **Define the Core Metrics:** Lock in the exact data points you will track for V1: Total Deaths, Total Injuries, Kidnappings (Count of people), Ransom Demanded, and Ransom Paid. (Metrics like IDPs and Infrastructure will be tabled for later versions).
    
- [ ] **Write the Methodology Page:** Draft a clear, public-facing document explaining:
    
    - What constitutes a "security incident" on your tracker.
        
    - How you handle conflicting numbers from different news sources (e.g., "We log the lowest confirmed number to avoid exaggeration, but link to all sources").
        
    - A disclaimer that data relies on publicly reported incidents, meaning actual figures are likely higher.
        

## Phase 2: Infrastructure & Database Setup

This phase sets up the "ephemeral" server environment and the permanent, secure database.

- [ ] **Provision a Linux VPS:** Rent a basic Ubuntu Linux machine from a provider like Hetzner, DigitalOcean, or Linode (a $5–$10/month instance with 1-2GB RAM is plenty to start).
    
- [ ] **Install Docker & Docker Compose:** SSH into your Linux machine and install the Docker engine. This will run your frontend and your Python AI scripts in isolated containers.
    
- [ ] **Create a MongoDB Atlas Account:** Sign up for the free tier (M0 cluster) on MongoDB Atlas. This provides 512MB of storage (enough for thousands of text-based incidents), automatic backups, and zero server management.
    
- [ ] **Configure Database Security:** Inside MongoDB Atlas, whitelist your Linux VPS's IP address so only your server can access the database. Generate a secure connection string URI.
    
- [ ] **Design the JSON Document Schema:** Define how an incident will look in the database.
    
    _Example Structure:_
    
    `{"date": "2026-05-20", "state": "Kaduna", "incident_type": "Kidnapping", "deaths": 2, "injuries": 0, "kidnapped": 15, "ransom_demanded": 50000000, "summary": "...", "sources": [{"url": "...", "publisher": "Premium Times"}]}`
    

## Phase 3: The AI Automation Pipeline (Backend)

This is the engine of your platform. A Python script will wake up every night, search the web, extract structured data, and save it to MongoDB.

- [ ] **Initialize the Python Environment:** Create a folder for your backend script, set up a virtual environment, and install necessary libraries: `pip install pymongo google-genai python-dotenv`.
    
- [ ] **Set up the Gemini API Client:** Obtain an API key from Google AI Studio.
    
- [ ] **Write the Daily Scraping Prompt:** Create a strict system prompt for Gemini. Tell it to search for security incidents in Nigeria over the last 24 hours. Instruct it to output **only** structured JSON matching your schema, ensuring it separates distinct events (e.g., a clash in Borno vs. a kidnapping in Zamfara).
    
- [ ] **Implement Google Search Grounding:** Use the `google-genai` SDK to enable real-time web search.
    
    _Implementation detail:_
    
    Python
    
    ```
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=YOUR_API_KEY)
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents='Search for reported killings, kidnappings, and terrorism incidents in Nigeria today. Return the data in a strict JSON array...',
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type="application/json"
        )
    )
    ```
    
- [ ] **Write the Database Insertion Logic:** Have the Python script parse the AI's JSON output, validate that the numbers are integers, and use `pymongo` to insert the records into your MongoDB Atlas database.
    
- [ ] **Containerize the Python Script:** Write a `Dockerfile` for this script.
    
- [ ] **Set up the Cron Job:** Configure the Linux server (or the Docker container itself using a library like `schedule`) to run this Python script automatically at 2:00 AM WAT every single day.
    

## Phase 4: Frontend Development (Next.js + Map)

This is where you build the user interface, utilizing modern React tools for a fast, responsive dashboard.

- [ ] **Scaffold the Next.js App:** Run `npx create-next-app@latest`. Choose TypeScript and Tailwind CSS.
    
- [ ] **Install UI Components:** Install `shadcn/ui` to quickly add beautifully styled, accessible components like Date Pickers, Cards, and Data Tables without writing CSS from scratch.
    
- [ ] **Integrate the Nigeria SVG Map:** Download a free, web-optimized blank SVG map of Nigeria. Convert the raw SVG paths into a React component. Ensure each state's `<path>` tag has an `onClick` handler and a dynamic `fill` color that changes when selected or hovered.
    
- [ ] **Build the Metrics Dashboard:** Create the top-level UI cards (Total Deaths, Total Injuries, Total Kidnapped).
    
- [ ] **Create the API Routes (Next.js Backend):** Write an API route in Next.js (e.g., `/api/incidents`) that connects to your MongoDB database. It should accept query parameters like `?state=Borno&startDate=2026-05-01&endDate=2026-05-20` and return the aggregated sums and the list of articles.
    
- [ ] **Wire the Map to the Data:** Write the React logic so that when a user clicks "Zamfara" on the SVG map, the dashboard instantly updates to show only Zamfara's metrics and incident articles.
    
- [ ] **Build the Incident Feed:** Below the map, create a scrolling feed of the AI-generated articles. Ensure every article prominently displays its citations and links out to the original news sources.
    

## Phase 5: The "Investigate Today" Feature

This feature allows users to query the AI in real-time about the current situation on the ground for a specific state.

- [ ] **Design the UI Component:** Add a prominent "Investigate Today" button next to the selected state's name on the dashboard.
    
- [ ] **Create the Live Query API Route:** Write a new Next.js API route (`/api/investigate`) that takes the selected state as a parameter.
    
- [ ] **Integrate Gemini with Search Grounding (Live):** In this API route, call the Gemini API again with Google Search Grounding enabled. The prompt should be: _"Search for breaking news regarding security, violence, or kidnappings in [Selected State], Nigeria today. Provide a concise, unbiased 3-sentence summary of the current situation and include markdown links to your sources."_
    
- [ ] **Build the Loading State & Modal:** Because web searches take a few seconds, build a nice loading animation (e.g., "Consulting live news sources..."). Once the Gemini API responds, display the text and citations in a clean modal window.
    

## Phase 6: Deployment & Maintenance

Bringing it all together onto your Linux VPS.

- [ ] **Write a `docker-compose.yml` File:** Create a single file that defines both of your containers: the Next.js web app (exposed to port 80/443) and the Python cron-job container.
    
- [ ] **Set up Environment Variables:** Create a `.env` file on your server securely storing your MongoDB URI and your Gemini API keys. Do not commit this to GitHub.
    
- [ ] **Configure Domain & SSL:** Point your domain name (e.g., `betternigeria.org`) to your VPS's IP address. Use a reverse proxy like Nginx or Caddy (which can also be run in Docker) to automatically generate free SSL certificates via Let's Encrypt.
    
- [ ] **Launch:** Run `docker compose up -d` on your server.
    
- [ ] **Test the Pipeline:** Manually trigger the Python script to ensure it successfully reads the web, formats the JSON, and populates the map. Click the "Investigate Today" button to ensure the live Gemini API is responding correctly.