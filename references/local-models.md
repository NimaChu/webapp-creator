# Local Model Runtime

Model-enabled apps remain static frontends. A local same-origin server owns model routing and keeps credentials out of delivered HTML.

## Configuration

Copy the generated `.webapp.local.example.json` to `.webapp.local.json`:

```json
{
  "chat": {
    "baseUrl": "http://127.0.0.1:11434/v1",
    "model": "your-chat-model",
    "apiKeyEnv": "",
    "timeoutSeconds": 120
  },
  "image": {
    "baseUrl": "http://127.0.0.1:8188/v1",
    "model": "your-image-model",
    "apiKeyEnv": "",
    "timeoutSeconds": 180
  }
}
```

Use an OpenAI-compatible base URL. Ollama and LM Studio can expose compatible local endpoints. For an authenticated endpoint, set `apiKeyEnv` to an environment variable name and put the credential only in that environment variable.

Never put `apiKey`, `token`, `password`, authorization headers, or other credentials in the JSON or HTML.

## Browser Routes

Chat:

```js
const response = await fetch('/runtime/ai/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [{ role: 'user', content: input }],
    temperature: 0.4,
    stream: true
  })
})
```

For streaming chat responses, parse OpenAI-compatible `text/event-stream`
events incrementally, stop at `data: [DONE]`, and retain a JSON response
fallback for compatible servers that ignore `stream`.

Image generation:

```js
const response = await fetch('/runtime/ai/image', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt,
    size: '1024x1024',
    response_format: 'b64_json'
  })
})
```

Read model status from `/runtime/health`. Do not expose environment values or credentials in its response.

## Multimodal Input

For image understanding, use an OpenAI-compatible content array containing `text` and `image_url` items. Validate file type and size before converting to a data URL. Resize very large images when the full resolution is unnecessary.

## Output Safety

Treat model output as untrusted. Render plain text with `textContent`. If rich HTML is required, sanitize it with a maintained sanitizer. Do not execute generated code automatically. Preserve user input after errors, allow cancellation, prevent duplicate submissions, and report connection failures in the result region.

## Run

```bash
python3 scripts/webapp.py serve <project> --open
```

Bind to `127.0.0.1` by default. Bind to another interface only when the user intentionally needs local-network access.
The runtime accepts only `localhost`, `127.0.0.1`, and `::1` Host headers by
default to resist DNS rebinding. For intentional local-network access, add each
exact hostname or address explicitly:

```bash
python3 scripts/webapp.py serve <project> \
  --host 0.0.0.0 \
  --allow-host <trusted-lan-hostname-or-address>
```

Never add `0.0.0.0` as an allowed Host header.
