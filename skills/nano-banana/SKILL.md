---
name: nano-banana
description: Generate images using the OpenRouter API with the Nano Banana model (Gemini 2.5 Flash Image). Use this skill whenever the user asks to generate, create, or make an image, picture, illustration, photo, or visual using OpenRouter or Nano Banana. Also trigger when the user wants AI image generation and has an OpenRouter API key available, even if they don't mention "Nano Banana" by name — any request like "make me a picture of...", "generate an image of...", or "create a visual of..." should use this skill.
---

Generate images via the OpenRouter API using the Nano Banana model (`google/gemini-2.5-flash-image`). The API key comes from the `OPENROUTER_API_KEY` environment variable.

## How it works

Send a chat completion request to OpenRouter with `response_format: {"type": "image"}`. The model returns a base64-encoded PNG in the `choices[0].message.images` array. Decode it and save to the working directory.

## Step-by-step

1. **Confirm the API key exists** — check that `OPENROUTER_API_KEY` is set in the environment. If missing, tell the user to set it and stop.

2. **Craft the prompt** — take the user's image description and turn it into a clear, detailed prompt. Add descriptive details (style, composition, mood) if the user's request is brief, to get a better result from the model.

3. **Call the API** — use `curl` to POST to `https://openrouter.ai/api/v1/chat/completions`:

```bash
curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.5-flash-image",
    "messages": [
      {
        "role": "user",
        "content": "<image prompt here>"
      }
    ],
    "response_format": {"type": "image"}
  }'
```

4. **Extract and save the image** — parse the JSON response with Python. The image is at `choices[0].message.images[0].image_url.url` as a `data:image/png;base64,...` string. Decode and write to a file in the current working directory.

Use a descriptive filename based on the prompt (e.g., `giraffe_hot_sauce.png`), keeping it short and lowercase with underscores. Always use `.png` extension.

5. **Show the image** — use the Read tool to display the saved image to the user so they can see the result immediately.

6. **Handle errors** — if the API returns an error (e.g., 402 insufficient credits, 429 rate limit), show the error message to the user clearly. Common issues:
   - `402`: Insufficient credits — direct user to https://openrouter.ai/settings/credits
   - `429`: Rate limited — wait a moment and retry once
   - Other errors: show the raw error message

## Example

User: "make an image of a cat wearing a top hat"

→ Prompt sent: "Generate an image of a cat wearing a top hat. The cat should look distinguished and elegant, with a sleek black top hat perched on its head."
→ Saved as: `cat_top_hat.png`
→ Display the image to the user with the Read tool

## Important notes

- Always use `google/gemini-2.5-flash-image` — this is the Nano Banana model. Never substitute a different model.
- Always include `"response_format": {"type": "image"}` — without this, the model returns text instead of an image.
- The Python extraction script should handle the full response parsing and base64 decoding in one step for reliability.
- One image per request. If the user wants multiple images, run multiple requests sequentially.
