# Eqai AI Bridge

Use this mode only when a published Eqai HTML tool needs platform-hosted text or image generation. The tool remains frontend-only: Eqai owns model routing and secrets.

## Package Shape

```text
tool-folder/
  app/
    index.html
  prompts/
    assistant.md
  eqai-tool.json
```

The HTML must load:

```html
<script src="/runtime-sdk/v1/eqai.js"></script>
```

The AI tool must be opened inside its Eqai tool page. Directly opening `app/index.html` cannot connect to the bridge.

## Contract

```json
{
  "schemaVersion": 1,
  "mode": "ai-enabled",
  "entry": "index.html",
  "bridgeVersion": 1,
  "ai": {
    "profiles": {
      "assistant": {
        "type": "text",
        "modelPolicy": "balanced",
        "systemPrompt": "prompts/assistant.md",
        "stream": true,
        "maxInputChars": 12000,
        "maxOutputTokens": 2000
      },
      "illustration": {
        "type": "image",
        "modelPolicy": "image-standard",
        "sizes": ["1024x1024", "1536x1024", "1024x1536"],
        "quality": "auto",
        "maxPromptChars": 8000,
        "maxImages": 1
      }
    }
  }
}
```

Text policies are `fast`, `balanced`, and `reasoning`. Image tools use `image-standard`. Do not add provider, endpoint, API-key, token, base-URL, or secret fields.

## Browser API

Connect once:

```js
const eqai = await Eqai.connect()
```

Generate text:

```js
const result = await eqai.ai.generateText({
  profile: 'assistant',
  input: userInput,
})
```

Stream text:

```js
const stream = await eqai.ai.streamText({ profile: 'assistant', input: userInput })
for await (const chunk of stream) output.textContent += chunk
```

Generate an image:

```js
const blob = await eqai.ai.generateImage({
  profile: 'illustration',
  prompt,
  size: '1024x1024',
  quality: 'auto',
})
image.src = URL.createObjectURL(blob)
```

Use `AbortController` when the interface offers cancellation. Disable duplicate submissions, report bridge errors in the result region, revoke replaced image object URLs, and never persist prompts or outputs unless the platform adds an explicit storage contract.

## Prompt Design

Keep server-owned system prompts concise and task-specific. Tell the model what shape the UI can render, such as JSON or concise Markdown. Do not claim access to company facts, files, approvals, or live systems that the tool does not provide in its input.

Treat model output as untrusted. Render plain text by default. If rich HTML is required, sanitize it with a proven sanitizer rather than assigning arbitrary output to `innerHTML`.
