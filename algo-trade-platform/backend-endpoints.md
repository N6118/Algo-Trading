# Backend API Endpoints

## Signal Generation Endpoints (`/signals`)

- **POST /**
  - Create a new signal generation entry.
  - Request body: `SignalGenerationCreate`
  - Response: `SignalGeneration`

- **GET /{signal_id}**
  - Get a specific signal by ID.
  - Response: `SignalGeneration`

- **GET /user/{user_id}**
  - Get all signals for a specific user.
  - Query params: `skip`, `limit`
  - Response: `List[SignalGeneration]`

- **GET /active/**
  - Get all active signals.
  - Response: `List[SignalGeneration]`

- **PUT /{signal_id}**
  - Update a signal.
  - Request body: `SignalGenerationUpdate`
  - Response: `SignalGeneration`

- **DELETE /{signal_id}**
  - Deactivate a signal.
  - Response: `SignalGeneration`

- **POST /{signal_id}/process**
  - Process a signal and generate orders.
  - Response: `bool`

---

## Trade Endpoints (`/api/trades`)

- **POST /trades**
  - Create a new trade.
  - Request body: `TradeCreateRequest`
  - Response: `TradeResponse`
  - Handles risk, compliance, and technical exceptions with appropriate HTTP status codes.

<!-- More trade endpoints can be added here as they are implemented. -->

---
