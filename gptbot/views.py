# gptbot/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from utils.search import answer_question
from django.shortcuts import render
# 대화 히스토리는 세션 기반으로 따로 관리하거나, 여기서는 임시로 구현
conversation_history = [{"role": "system", "content": "hi"}]

@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode())
            user_input = body.get("user_input", "")
            if not user_input:
                return JsonResponse({"error": "No input"}, status=400)
            
            conversation_history.append({"role": "user", "content": user_input})
            full_answer = answer_question(user_input, conversation_history)
            conversation_history.append({"role": "assistant", "content": full_answer})

            # JSON 파싱 시도
            try:
                parsed = json.loads(full_answer)
                only_response = parsed.get("response", "no response")
            except json.JSONDecodeError:
                only_response = "응답 형식이 올바르지 않습니다."

            return JsonResponse({"answer": only_response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "POST method required"}, status=405)
@csrf_exempt
def chat_page(request):
    return render(request, "chat.html")
