# Yojana-Setu-BACKEND

M4 scheme data collection + WhatsApp integration for YojanaSetu.

## Repository Structure

```
Yojana-Setu-BACKEND/
├── data/
│   ├── scheme_schema.json          # JSON Schema for scheme records
│   ├── rules_schema.json           # JSON Schema for eligibility rules
│   ├── documents_schema.json       # JSON Schema for document requirements
│   ├── tutorials_schema.json       # JSON Schema for tutorial steps
│   ├── canonical_values.json       # Provisional MVP enumerated values
│   └── schemes/                    # 15 scheme JSON files (source of truth)
├── scripts/
│   ├── validate_data.py            # Validate scheme JSONs against schemas
│   └── generate_seed.py            # Generate supabase/seed.sql from JSONs
├── supabase/
│   ├── seed.sql                    # Auto-generated PostgreSQL seed
│   └── migrations/                 # Database schema migrations
├── whatsapp/                       # WhatsApp Cloud API integration (M4)
│   ├── app.py                      # FastAPI app with webhook endpoints
│   ├── config.py                   # Environment variable configuration
│   ├── webhook.py                  # Webhook verification + message parsing
│   ├── handlers.py                 # Message routing + response building
│   ├── scheme_service.py           # Reads scheme JSONs, provides lookups
│   ├── m2_client.py                # M2 eligibility API client
│   ├── message_utils.py            # Message splitting for 4096-char limit
│   └── templates.py                # WhatsApp message text templates
├── tests/                          # Test suite
│   ├── test_app.py                 # FastAPI endpoint integration tests
│   ├── test_webhook.py
│   ├── test_handlers.py
│   ├── test_scheme_service.py
│   ├── test_m2_client.py
│   ├── test_config.py
│   └── test_message_utils.py
├── requirements.txt
├── .env.example
└── README.md
```

## Data Pipeline

```
data/schemes/*.json → validate_data.py → generate_seed.py → supabase/seed.sql
```

### Validate data

```bash
python3 scripts/validate_data.py
```

### Regenerate seed

```bash
python3 scripts/generate_seed.py
```

## WhatsApp Integration

### How It Works

The WhatsApp bot receives messages via the WhatsApp Cloud API webhook, routes them through the handler, and responds using scheme data from `data/schemes/*.json`.

Architecture:

```
WhatsApp User
    ↓
WhatsApp Cloud API
    ↓
M4 WhatsApp Webhook (FastAPI)
    ↓
M4 Handler + Scheme Service (reads JSON files)
    ↓
Response back to WhatsApp User

For eligibility:
M4 Handler → M2 Eligibility API → M2 Engine → Response
```

### Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your WhatsApp Cloud API credentials
```

### Run Locally

```bash
uvicorn whatsapp.app:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WHATSAPP_VERIFY_TOKEN` | Yes | Token for webhook verification |
| `WHATSAPP_ACCESS_TOKEN` | Yes | WhatsApp Cloud API access token |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes | Phone number ID from Meta |
| `WHATSAPP_APP_SECRET` | No | App secret for signature verification |
| `GRAPH_API_VERSION` | No | Meta Graph API version (default: v23.0) |
| `M2_BACKEND_URL` | No | M2 backend URL (default: http://localhost:8000) |
| `M2_TIMEOUT` | No | M2 request timeout in seconds (default: 10) |
| `M2_API_KEY` | No | API key for M2 backend |

### Webhook Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/webhook` | WhatsApp webhook verification |
| POST | `/webhook` | Receive incoming WhatsApp messages |
| GET | `/health` | Health check |

### Configure in Meta Developer Portal

1. Set webhook URL to: `https://your-domain/webhook`
2. Set verify token to match `WHATSAPP_VERIFY_TOKEN`
3. Subscribe to: `messages`

## Meta WhatsApp Cloud API Setup

Step-by-step guide to connect this bot to the Meta WhatsApp Cloud API.

### What You Need from Meta

1. **Meta Developer Account** — Sign up at [developers.facebook.com](https://developers.facebook.com)
2. **WhatsApp Business App** — Create one in the Meta Developer Portal under *My Apps*
3. **Phone Number ID** — Found in *WhatsApp > Getting Started > Phone numbers*. This is the number your bot sends from.
4. **Permanent Access Token** — Go to *System Users > Generate Token* (not the temporary token from the quick-start page). It must have the `whatsapp_business_messaging` permission.
5. **App Secret** — Found in *App Settings > Basic > App Secret*. Used to verify incoming webhook signatures.
6. **Verify Token** — You make this up. Any string works (e.g. `yojanasetu-verify-2024`). You will enter the same string in both your `.env` file and the Meta dashboard.

### Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Where to find it | Example |
|----------|-----------------|---------|
| `WHATSAPP_VERIFY_TOKEN` | You invent this (any string) | `yojanasetu-verify-2024` |
| `WHATSAPP_ACCESS_TOKEN` | Meta Portal > System Users > Token | `EAAI...xyz` |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta Portal > WhatsApp > Phone numbers | `1234567890` |
| `WHATSAPP_APP_SECRET` | Meta Portal > App Settings > Basic > App Secret | `abc123...` |
| `GRAPH_API_VERSION` | Meta Graph API docs (default: `v23.0`) | `v23.0` |

### Connecting the Webhook

1. Deploy the bot to a public HTTPS endpoint (e.g. `https://yourdomain.com`)
2. In the Meta Developer Portal, go to **WhatsApp > Configuration > Webhook**
3. Enter your webhook URL: `https://yourdomain.com/webhook`
4. Enter the **Verify Token** — must match `WHATSAPP_VERIFY_TOKEN` in your `.env`
5. Click **Verify and Save**
6. Subscribe to the `messages` field

### Testing the Connection

1. Start the bot: `uvicorn whatsapp.app:app --host 0.0.0.0 --port 8000`
2. Send a WhatsApp message (e.g. "Hi") to your phone number
3. The bot should reply with the welcome menu
4. Check server logs for any errors

### Troubleshooting

| Problem | Fix |
|---------|-----|
| Webhook verification fails | Ensure `WHATSAPP_VERIFY_TOKEN` matches the token in Meta dashboard |
| Bot doesn't reply | Check `WHATSAPP_ACCESS_TOKEN` is a permanent token, not temporary |
| Signature errors | Ensure `WHATSAPP_APP_SECRET` is correct and matches Meta dashboard |
| 404 on webhook | Verify the bot is running and the URL includes `/webhook` |
| Rate limit (429) | Bot handles this gracefully — waits and stops sending further chunks |

### Current MVP Flow

User sends "Hi" → Bot responds with menu:

1. **Find schemes** → Lists all 15 government schemes
2. **Check eligibility** → Checks eligibility via M2 backend
3. **Required documents** → Shows documents for selected scheme
4. **How to apply** → Shows application tutorial steps

Additional commands:
- Select scheme by number → Shows scheme details, benefits, URL
- `0` → Return to main menu

### Supported Commands

| User Input | Action |
|------------|--------|
| Hi, Hello, Start, Menu, 0 | Show welcome menu |
| 1, Find schemes, Schemes | List all schemes |
| Number (1-15) | Select scheme and show details |
| 2, Eligibility | Check eligibility (delegated to M2) |
| 3, Documents | Show required documents |
| 4, Apply, Tutorial | Show application steps |
| Help, ? | Show help/fallback |

### Testing

```bash
python3 -m pytest tests/ -v
```

Tests cover:
- Webhook verification (valid/invalid tokens)
- Incoming message parsing
- Menu routing and state management
- Scheme lookup from M4 JSON data
- Document and tutorial lookup
- M2 client real HTTP integration with error handling
- Unknown message handling
- Session isolation between users
- Config loading and graph API version
- Message splitting at 4096-char WhatsApp limit
- Error body masking for secrets
- FastAPI endpoint integration (health, GET/POST /webhook)
- Eligibility result templates (eligible/not eligible/potentially eligible/error)

## M2 Integration Boundary

The WhatsApp bot does NOT evaluate eligibility. It delegates to M2 via `whatsapp/m2_client.py`, which makes a real HTTP call to the M2 backend.

### M2 API Endpoint

- **Endpoint**: `POST {M2_BACKEND_URL}/eligibility/check`
- **Auth**: None (no auth required)
- **Timeout**: Configurable via `M2_TIMEOUT` (default 10s)

### Request Schema

```json
{
  "scheme_code": "pm_kisan",
  "profile": {}
}
```

When the user provides additional details (e.g. `eligibility age:30,land:true`), these are parsed into the `profile` object:

```json
{
  "scheme_code": "pm_kisan",
  "profile": {
    "age": 30,
    "land": true
  }
}
```

If no profile data is provided, an empty `{}` profile is sent. M2 returns `missing_fields` that the user is prompted to fill in.

### Response Schema

```json
{
  "scheme_code": "pm_kisan",
  "status": "Eligible | Potentially Eligible | Not Eligible",
  "eligible": true | false | null,
  "reason_codes": ["EXCLUSION_TRIGGERED"],
  "reasons": ["Persons who paid income tax are excluded."],
  "missing_fields": ["has_cultivable_land_in_name", "is_nri"],
  "evaluated_rules": []
}
```

### Error Handling

| Condition | HTTP status | Result |
|-----------|-------------|--------|
| Scheme not found | 404 | `error_type: "scheme_not_found"` |
| Missing/invalid request | 400-499 | `error_type: "bad_request"` |
| Backend down | 5xx | `error_type: "server_error"` |
| Connect failure | — | `error_type: "backend_unavailable"` |
| Timeout | — | `error_type: "timeout"` |
| Malformed response | — | `error_type: "invalid_response"` |

All error responses return safe, user-facing messages (no internal details or tokens leaked).

### How the Bot Routes Eligibility Responses

| M2 Status | Bot Template |
|-----------|-------------|
| `Eligible` | Shows confirmation with reasons |
| `Not Eligible` | Shows reasons for ineligibility |
| `Potentially Eligible` | Shows missing fields + profile hint |
| Error | Shows friendly error message with retry guidance |

### Configuration

`.env`:

```
M2_BACKEND_URL=http://localhost:8000
M2_TIMEOUT=10
M2_API_KEY=
```

## Important Constraints

- M4 owns WhatsApp integration only
- M2 owns the central backend and eligibility engine
- M4 does NOT implement a separate eligibility engine
- M4 does NOT hard-code eligibility decisions
- WhatsApp calls M2's eligibility API
- All scheme data comes from `data/schemes/*.json` (no invented data)
