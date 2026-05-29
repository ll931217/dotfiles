# Code change verifications

## Frontend

- Use `agent-browser` CLI to verify frontend functionality works as intended
- If the frontend requires certain credentials, either:
  - Ask user to start a chrome in debug mode and fill in the credentials
  - Ask the user for the credentials

## Backend

- Use `jsonl` logs for each verification
- Use `openlogs` CLI as another way to verify changes.
