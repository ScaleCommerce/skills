#!/usr/bin/env python3
"""Nano Banana CLI — thin wrapper around the OpenRouter API for image generation."""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://openrouter.ai/api/v1"
MODEL = "google/gemini-3.1-flash-image-preview"

ASPECT_RATIOS = ["1:1", "16:9", "9:16", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "21:9"]


def _api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return key


def _request(method, path, body=None):
    url = f"{API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        try:
            err = json.dumps(json.loads(err), indent=2)
        except Exception:
            pass
        print(f"API error {e.code}:\n{err}", file=sys.stderr)
        sys.exit(1)


def _encode_image(path):
    """Read an image file and return a data URL."""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def _build_image_config(args):
    cfg = {}
    if getattr(args, "aspect_ratio", None):
        cfg["aspect_ratio"] = args.aspect_ratio
    if getattr(args, "image_size", None):
        cfg["image_size"] = args.image_size
    return cfg or None


def _extract_and_save(resp, output_path):
    """Pull the base64 image from the API response and write it to disk."""
    try:
        img_url = resp["choices"][0]["message"]["images"][0]["image_url"]["url"]
    except (KeyError, IndexError):
        print(json.dumps(resp, indent=2), file=sys.stderr)
        print("Error: no image in response", file=sys.stderr)
        sys.exit(1)

    b64 = img_url.split(",", 1)[1]
    img_bytes = base64.b64decode(b64)

    with open(output_path, "wb") as f:
        f.write(img_bytes)

    return img_bytes


def _result_json(output_path, img_bytes, resp):
    gen_id = resp.get("id", "")
    tokens = resp.get("usage", {})
    return {
        "file": output_path,
        "bytes": len(img_bytes),
        "generation_id": gen_id,
        "prompt_tokens": tokens.get("prompt_tokens"),
        "completion_tokens": tokens.get("completion_tokens"),
    }


def _numbered_path(base_path, i, count):
    """Return base_path for count=1, or insert _1, _2, ... before extension."""
    if count == 1:
        return base_path
    stem, ext = os.path.splitext(base_path)
    return f"{stem}_{i + 1}{ext}"


def cmd_generate(args):
    """Generate image(s) from a text prompt."""
    image_config = _build_image_config(args)
    results = []

    for i in range(args.count):
        body = {
            "model": MODEL,
            "messages": [{"role": "user", "content": args.prompt}],
            "response_format": {"type": "image"},
        }
        if image_config:
            body["image_config"] = image_config

        resp = _request("POST", "/chat/completions", body)
        out = _numbered_path(args.output, i, args.count)
        img_bytes = _extract_and_save(resp, out)
        results.append(_result_json(out, img_bytes, resp))

    print(json.dumps(results if len(results) > 1 else results[0]))


def cmd_edit(args):
    """Edit an existing image with a text prompt."""
    data_url = _encode_image(args.input)
    image_config = _build_image_config(args)

    content = [
        {"type": "image_url", "image_url": {"url": data_url}},
        {"type": "text", "text": args.prompt},
    ]

    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "response_format": {"type": "image"},
    }
    if image_config:
        body["image_config"] = image_config

    resp = _request("POST", "/chat/completions", body)
    img_bytes = _extract_and_save(resp, args.output)
    print(json.dumps(_result_json(args.output, img_bytes, resp)))


def cmd_balance(args):
    resp = _request("GET", "/key")
    data = resp.get("data", resp)
    print(json.dumps({
        "limit": data.get("limit"),
        "limit_remaining": data.get("limit_remaining"),
        "usage": data.get("usage"),
    }, indent=2))


def cmd_stats(args):
    resp = _request("GET", f"/generation?id={args.id}")
    d = resp.get("data", resp)
    print(json.dumps({
        "model": d.get("model"),
        "total_cost": d.get("total_cost"),
        "latency_ms": d.get("latency"),
        "tokens_prompt": d.get("tokens_prompt"),
        "tokens_completion": d.get("tokens_completion"),
    }, indent=2))


def main():
    p = argparse.ArgumentParser(prog="nb", description="Nano Banana CLI")
    sub = p.add_subparsers(dest="command", required=True)

    # generate
    gen = sub.add_parser("generate", help="Generate an image from a text prompt")
    gen.add_argument("prompt", help="Image description")
    gen.add_argument("-o", "--output", required=True, help="Output PNG path")
    gen.add_argument("-n", "--count", type=int, default=1, help="Number of variations")
    gen.add_argument("--aspect-ratio", choices=ASPECT_RATIOS)
    gen.add_argument("--image-size", choices=["1K", "2K", "4K"])
    gen.set_defaults(func=cmd_generate)

    # edit
    ed = sub.add_parser("edit", help="Edit an existing image with a text prompt")
    ed.add_argument("prompt", help="Edit instruction")
    ed.add_argument("-i", "--input", required=True, help="Input image path")
    ed.add_argument("-o", "--output", required=True, help="Output PNG path")
    ed.add_argument("--aspect-ratio", choices=ASPECT_RATIOS)
    ed.add_argument("--image-size", choices=["1K", "2K", "4K"])
    ed.set_defaults(func=cmd_edit)

    # balance
    bal = sub.add_parser("balance", help="Check API key balance")
    bal.set_defaults(func=cmd_balance)

    # stats
    st = sub.add_parser("stats", help="Get generation stats")
    st.add_argument("id", help="Generation ID")
    st.set_defaults(func=cmd_stats)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
