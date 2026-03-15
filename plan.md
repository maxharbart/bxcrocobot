# Bitrix24 Crocodile Game Bot -- Agent‑Optimized Implementation Spec

Version: 1.0\
Target: Coding Agents / Autonomous Dev Systems

Inspired by: https://github.com/Roninore/crocodile_tg

------------------------------------------------------------------------

# 1. Project Goal

Create a **multiplayer Crocodile (Pictionary-style) game bot for
Bitrix24 chat**.

The bot should:

• run as an external service\
• integrate through Bitrix REST API + webhooks\
• manage multiplayer sessions per chat\
• store game state in Redis\
• send private messages to the drawing player

The bot must support **multiple simultaneous chats**.

------------------------------------------------------------------------

# 2. Technology Stack

Recommended stack (agent should follow unless constraints appear):

Backend - Python 3.11+ - FastAPI - Uvicorn

Storage - Redis

Infrastructure - Docker - Nginx (production)

Libraries - redis - requests - pydantic

Optional - bitrixogram

------------------------------------------------------------------------

# 3. High-Level Architecture

Bitrix Chat\
↓\
Webhook Event\
↓\
FastAPI Listener\
↓\
Command Dispatcher\
↓\
Game Engine\
↓\
Redis Storage\
↓\
Bitrix REST API

------------------------------------------------------------------------

# 4. Functional Requirements

## Game lifecycle

1.  Create game
2.  Players join
3.  Round starts
4.  Drawer receives secret word
5.  Players guess
6.  Correct guess → score update
7.  Round ends
8.  Next round begins

------------------------------------------------------------------------

# 5. Commands

  Command      Description
  ------------ -------------------
  /crocodile   create new game
  /join        join game
  /leave       leave game
  /start       start first round
  /skip        skip word
  /score       show leaderboard
  /stop        stop game

------------------------------------------------------------------------

# 6. Event Handling

Bitrix sends webhook events when messages are sent.

Endpoint:

POST /bitrix/events

Example event payload:

    {
      "event": "ONIMBOTMESSAGEADD",
      "data": {
        "MESSAGE": "/join",
        "FROM_USER_ID": 123,
        "CHAT_ID": 45
      }
    }

Dispatcher pseudocode:

    message = payload.MESSAGE

    if message.startswith("/"):
        handle_command()

    else:
        handle_guess()

------------------------------------------------------------------------

# 7. Core Components

## 1. Bitrix Client

Responsible for API communication.

Functions:

send_chat_message(chat_id, text)

send_private_message(user_id, text)

get_user_info(user_id)

------------------------------------------------------------------------

## 2. Game Manager

Responsible for managing sessions.

Functions:

create_game(chat_id)

add_player(chat_id, user_id)

remove_player(chat_id, user_id)

start_round(chat_id)

end_round(chat_id)

check_guess(chat_id, message)

------------------------------------------------------------------------

## 3. Word Service

Load word dictionary.

Functions:

load_words()

get_random_word()

Word list stored in:

words.txt

Example:

    elephant
    airplane
    pizza
    volcano
    penguin

------------------------------------------------------------------------

## 4. Timer Service

Manages round timeout.

Example:

round_length = 90 seconds

If time expires:

round ends automatically.

------------------------------------------------------------------------

# 8. Redis Data Model

Each chat has a separate game state.

Key:

    game:{chat_id}

Example structure:

    {
     "players": [1,2,3],
     "scores": {
       "1": 10,
       "2": 5
     },
     "round": 2,
     "drawer": 1,
     "word": "elephant",
     "status": "active"
    }

Additional keys:

    timer:{chat_id}

------------------------------------------------------------------------

# 9. Game Flow

## Create Game

User:

/crocodile

Bot:

"Game created. Players join using /join"

------------------------------------------------------------------------

## Join Game

User:

/join

Bot:

"Player added"

------------------------------------------------------------------------

## Start Round

Bot selects drawer randomly.

Bot selects word.

Bot sends private message:

"Your word: ELEPHANT"

Chat message:

"Round started. Guess the word!"

------------------------------------------------------------------------

## Guess Handling

Every non-command message is treated as guess.

Algorithm:

    if guess.lower() == word.lower():
        winner = user

Actions:

• announce winner\
• update score\
• end round

------------------------------------------------------------------------

## Scoreboard

Command:

/score

Example output:

    Leaderboard

    Alice — 20
    Bob — 15
    John — 5

------------------------------------------------------------------------

# 10. API Layer (FastAPI)

Required routes:

    POST /bitrix/events
    POST /bitrix/install
    GET  /health

Example FastAPI skeleton:

    @app.post("/bitrix/events")
    async def bitrix_event(payload: dict):
        process_event(payload)

------------------------------------------------------------------------

# 11. Error Handling

Agent must implement:

• missing game state\
• duplicate joins\
• empty player list\
• invalid commands

Example:

    if user already joined:
        return "You already joined"

------------------------------------------------------------------------

# 12. Concurrency

Multiple chats may run games simultaneously.

Therefore:

chat_id must be used as isolation key.

All Redis keys must include chat_id.

------------------------------------------------------------------------

# 13. Security

Required:

• verify Bitrix webhook signature (if available) • reject unknown events
• sanitize user input

------------------------------------------------------------------------

# 14. Deployment

## Local Development

Install dependencies:

    pip install fastapi uvicorn redis requests

Run:

    uvicorn app:app --reload

------------------------------------------------------------------------

# 15. Docker Deployment

Dockerfile:

    FROM python:3.11

    WORKDIR /app

    COPY . .

    RUN pip install fastapi uvicorn redis requests

    CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]

Build:

    docker build -t bitrix-crocodile-bot .

Run:

    docker run -p 8000:8000 bitrix-crocodile-bot

------------------------------------------------------------------------

# 16. Bitrix Setup

Steps:

1.  Open Bitrix24
2.  Go to Developer Resources
3.  Create Local Application

Configure:

Handler URL

    https://yourserver.com/bitrix/events

Install URL

    https://yourserver.com/bitrix/install

Save credentials.

Add bot to chat.

------------------------------------------------------------------------

# 17. Acceptance Criteria

Agent implementation is complete when:

✔ Game can be created in Bitrix chat\
✔ Players can join\
✔ Drawer receives private word\
✔ Guesses work\
✔ Scoreboard updates\
✔ Multiple chats supported\
✔ Redis persistence works

------------------------------------------------------------------------

# 18. Recommended Implementation Order

Step 1 --- Webhook server\
Step 2 --- Bitrix API client\
Step 3 --- Redis game state\
Step 4 --- Command dispatcher\
Step 5 --- Game engine\
Step 6 --- Guess validation\
Step 7 --- Scoreboard\
Step 8 --- Round timers\
Step 9 --- Docker deployment

------------------------------------------------------------------------

# 19. Optional Enhancements

Not required for MVP.

Possible extensions:

• drawing board integration\
• emoji reactions\
• difficulty levels\
• word categories\
• AI hint generator\
• daily leaderboard

------------------------------------------------------------------------

# 20. Deliverables

The coding agent must produce:

Project repository containing:

    README.md
    app.py
    bitrix_client.py
    game/
    handlers/
    services/
    storage/
    Dockerfile
    requirements.txt
    words.txt

The repository must be runnable with:

    docker build
    docker run
