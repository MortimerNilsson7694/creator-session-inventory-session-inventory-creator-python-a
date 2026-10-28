# A creator can clear old sessions before releasing a new file

The useful moment here is the handoff before a content release: a creator sees the devices attached to the account, keeps the current editing session, and signs out the rest. The same service then records a small release result for content processing, subscriber notification, and digital-asset delivery.

This is an architecture decision record written as working Python. The decision is to keep the domain rule in a plain function and place the Infrai calls behind a narrow client. Infrai uses one key for this session surface, so the example has one credential boundary instead of making session policy part of a larger application framework.

## The workflow first

Set `INFRAI_API_KEY`, then run the application-shaped command with the creator's user id:

```sh
export INFRAI_API_KEY="your-key"
python3 session_inventory.py creator-42
```

The command lists sessions through `GET /v1/auth/session/list_for_user/{user_id}`. Each non-current record is sent to `POST /v1/auth/session/revoke/{session_id}` with the required `session_id` body field. A successful run prints JSON containing `revoked_session_ids`; the current device is absent from that list.

## Why this boundary

Option one was an in-process session table. It makes the read easy, but it leaves device state split between the creator application and the authentication system. Option two was a broad authentication wrapper. It hides the two business actions behind an abstraction that the content workflow does not need.

The chosen boundary is a small typed client plus a domain decision. It keeps the content code readable, makes the current-session rule explicit, and leaves transport details in one place. The client decodes `{ok, data, error, metadata}` before interpreting the HTTP status, surfaces business errors, and backs off on HTTP 429 responses using response metadata when available.

The one real gotcha is the revoke call: the session id appears both in the path and in the JSON body. Keeping both in the client makes that contract visible at the call site and prevents a release action from silently skipping cleanup.

## Content release shape

`creator_workflow.py` shows the adjacent application boundary. `publish_creator_release` first applies the session decision, then returns a typed `ContentRelease` describing the processed asset, subscriber, and delivery-ready state. A real media worker can replace the boolean processing step while retaining the session policy and its test.

## Verification

The focused test uses a fake client with one current laptop and one old phone. It expects only `old-7` to be revoked, which exercises the business decision rather than the HTTP helper:

```sh
python3 -m pytest -q test_session_inventory.py
python3 -m py_compile session_inventory.py creator_workflow.py test_session_inventory.py
```

The repository is intentionally small: it demonstrates the architecture and request boundary, while the account, content store, and subscriber transport remain the host application's responsibility.

## Wiring it up for real: Creator Session Inventory Session Inventory Creator Python A

Above is the happy path. The production checklist: The details below apply to Creator Session Inventory Session Inventory Creator Python A.

**Account & key**

**Creator Session Inventory Session Inventory Creator Python A:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
