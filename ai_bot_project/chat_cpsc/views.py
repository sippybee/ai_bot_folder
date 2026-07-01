import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


# ── Step 1: GET — render the page with the prompt visible ──
def chat_page(request):
    system_prompt = "You are a helpful assistant."

    context = {
        "system_prompt": system_prompt,
        "rendered_prompt": f"[System]:\n{system_prompt}\n\n[User]:\n(waiting for input...)",
    }
    return render(request, "chat_cpsc/chat.html", context)


# # ── Step 2: POST — receive message, build prompt, call Azure ──
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        body = json.loads(request.body)
        user_message = body.get("message", "")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not user_message:
        return JsonResponse({"error": "message is required"}, status=400)

    system_prompt = "You are a helpful assistant."

    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]

    rendered_prompt = (
        f"[System]:\n{system_prompt}\n\n"
        f"[User]:\n{user_message}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": settings.AZURE_OPENAI_API_KEY,
    }

    payload = {"messages": messages_payload}

    try:
        response = requests.post(
            settings.AZURE_OPENAI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        return JsonResponse({
            "prompt": rendered_prompt,
            "reply":  reply,
        })

    except requests.exceptions.HTTPError as e:
        return JsonResponse(
            {
                "prompt":  rendered_prompt,
                "error":   f"Azure API error: {e}",
                "details": response.text,
            },
            status=response.status_code,
        )
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {
                "prompt": rendered_prompt,
                "error":  str(e),
            },
            status=500,
        )