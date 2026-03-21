---
name: nano-banana
description: Generate images using the OpenRouter API with the Nano Banana model (Gemini 2.5 Flash Image). Use this skill whenever the user asks to generate, create, or make an image, picture, illustration, photo, or visual using OpenRouter or Nano Banana. Also trigger when the user wants AI image generation and has an OpenRouter API key available, even if they don't mention "Nano Banana" by name — any request like "make me a picture of...", "generate an image of...", or "create a visual of..." should use this skill. Also trigger for image editing requests like "remove the background", "change the color", "add X to this image".
---

Generate and edit images via the OpenRouter API using the Nano Banana model (`google/gemini-3.1-flash-image-preview`). The API key comes from the `OPENROUTER_API_KEY` environment variable.

## CLI

All API interactions go through the bundled CLI at `scripts/nb.py` (relative to this skill). This keeps token usage minimal — no need to craft curl commands or write inline Python. The CLI uses only stdlib (no pip install needed).

```bash
NB="python3 <skill-path>/scripts/nb.py"
```

### generate — create an image from a text prompt

```bash
$NB generate "A cat wearing a top hat, distinguished and elegant" -o cat_top_hat.png
$NB generate "Mountain sunset" -o sunset.png --aspect-ratio 16:9 --image-size 4K
$NB generate "Logo concepts for a coffee shop" -o logo.png -n 3  # creates logo_1.png, logo_2.png, logo_3.png
```

Options:
- `-o, --output` (required) — output PNG path
- `-n, --count` — number of variations (default: 1). Files get `_1`, `_2` suffixes.
- `--aspect-ratio` — `1:1` (default), `16:9`, `9:16`, `3:2`, `2:3`, `3:4`, `4:3`, `4:5`, `5:4`, `21:9`
- `--image-size` — `1K` (default), `2K`, `4K`

### edit — modify an existing image with a text instruction

Sends the input image + prompt to the model. Use for background removal, color changes, adding/removing elements, style transfer, etc.

```bash
$NB edit "Remove the background and make it transparent" -i photo.jpg -o photo_nobg.png
$NB edit "Change the sky to a dramatic sunset" -i landscape.png -o landscape_sunset.png
$NB edit "Apply a watercolor painting style" -i photo.jpg -o watercolor.png
```

Options:
- `-i, --input` (required) — input image path (any common format)
- `-o, --output` (required) — output PNG path
- `--aspect-ratio` / `--image-size` — same as generate

### balance — check API key credits

```bash
$NB balance
```

### stats — get cost/latency for a generation

```bash
$NB stats <generation_id>
```

All commands return JSON to stdout. Errors go to stderr with non-zero exit.

## Workflow

1. **Craft the prompt** — take the user's description and enrich it with style, composition, and mood details. Keep it concise but vivid.

2. **Pick the right command** — `generate` for new images, `edit` for modifying existing ones.

3. **Choose a filename** — descriptive, lowercase, underscores, `.png` extension (e.g., `sunset_mountains.png`).

4. **Set aspect ratio** when the content has a natural shape — `16:9` for landscapes/headers, `9:16` for phone wallpapers/stories, `1:1` for avatars/social, `4:3` for presentations.

5. **Run the CLI** and then **show the image** with the Read tool so the user sees it immediately.

6. **Handle errors**:
   - `402`: Insufficient credits — direct user to https://openrouter.ai/settings/credits
   - `429`: Rate limited — wait briefly and retry once

## Examples

**Generate:**
User: "make an image of a cat wearing a top hat"

```bash
$NB generate "A distinguished cat wearing a sleek black top hat, elegant portrait style, soft studio lighting" -o cat_top_hat.png
```

**Edit:**
User: "can you make the background blurry in this photo?" (user has `portrait.jpg`)

```bash
$NB edit "Blur the background with a shallow depth-of-field bokeh effect, keep the subject sharp" -i portrait.jpg -o portrait_blurred.png
```

**Variations:**
User: "give me a few options for a hero image for my coffee shop landing page"

```bash
$NB generate "Warm inviting coffee shop interior, morning light streaming through windows, artisan coffee cups on wooden counter" -o hero.png -n 3 --aspect-ratio 16:9 --image-size 4K
```

## Notes

- One image per API call. `-n 3` makes 3 sequential calls.
- The `edit` command accepts any common image format as input (PNG, JPG, WebP, etc.) but always outputs PNG.
- The CLI handles all base64 encoding/decoding, error parsing, and file writing internally.
