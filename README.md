# Assort Health Voice Agent

A medical appointment scheduling voice agent that allows patients to schedule appointments via phone calls. The agent collects patient information, validates addresses, offers available appointment slots, and sends confirmation emails.

## Technology Stack

- **Telephony**: Twilio for phone number hosting and call handling
- **Voice Agent**: LiveKit for advanced voice agent capabilities including:
  - **Speech-to-Text**: Integrated with Deepgram for accurate speech recognition
  - **Text-to-Speech**: Integrated with ElevenLabs for natural-sounding voice synthesis
  - **AI Brain**: Integrated with OpenAI for natural language understanding

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd assort-health-voice-agent
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example environment file and fill in your credentials:
   ```
   cp .env.example .env
   ```

5. Run the application:
   ```
   python app.py start
   ```
