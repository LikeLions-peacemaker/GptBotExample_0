import pandas as pd
import numpy as np
import json
from gptbot.models import Embedding  # 모델 import
from openai import OpenAI
from typing import List
from scipy import spatial
from dotenv import load_dotenv
load_dotenv()
client = OpenAI()

def load_embeddings_df():
    # DB에서 임베딩 전체 조회 (n_tokens 필드가 모델에 없으면 아래에서 계산)
    qs = Embedding.objects.all().values('text', 'embedding')
    rows = []
    for obj in qs:
        text = obj['text']
        embedding = json.loads(obj['embedding'])  # 문자열 → 리스트
        n_tokens = len(text)  # 필요시 tiktoken으로 교체
        rows.append({'text': text, 'embeddings': embedding, 'n_tokens': n_tokens})
    return pd.DataFrame(rows)

def distances_from_embeddings(
    query_embedding: List[float],
    embeddings: List[List[float]],
    distance_metric="cosine",
) -> List[float]:
    """Return the distances between a query embedding and a list of embeddings."""
    distance_metrics = {
        "cosine": spatial.distance.cosine,
        "L1": spatial.distance.cityblock,
        "L2": spatial.distance.euclidean,
        "Linf": spatial.distance.chebyshev,
    }
    distances = [
        distance_metrics[distance_metric](query_embedding, embedding)
        for embedding in embeddings
    ]
    return distances

def create_context(question, df, max_len=1800):
    """질문과 학습 데이터를 비교해 컨텍스트를 만드는 함수"""

    # 질문을 벡터화
    q_embeddings = client.embeddings.create(
        input=[question], model='text-embedding-3-small'
    ).data[0].embedding

    # 코사인 유사도 계산
    df['distances'] = distances_from_embeddings(
        q_embeddings,
        df['embeddings'].values,  # 이미 np.array(embedding) 형태임
        distance_metric='cosine'
    )

    returns = []
    cur_len = 0

    # 유사도 순으로 정렬, 토큰 개수 한도 내에서 텍스트 추가
    for _, row in df.sort_values('distances', ascending=True).iterrows():
        cur_len += row['n_tokens'] + 4
        if cur_len > max_len:
            break
        returns.append(row["text"])

    return "\n\n###\n\n".join(returns)

def answer_question(question, conversation_history):
    """문맥에 따라 질문에 JSON으로 정답하는 기능"""

    df = load_embeddings_df()
    context = create_context(question, df, max_len=200)

    system_prompt = """
당신은 친절하고 신뢰할 수 있는 법률 안내 챗봇 'Law Helper'입니다.

사용자의 질문을 분석하여 반드시 아래 형식의 **JSON**으로만 응답하세요.

- JSON만 출력하며, 텍스트 해설이나 서문 없이 중괄호(`{{ }}`) 포함된 JSON만 응답해야 합니다.
- 각 필드에 해당하지 않으면 `"unknown"` 또는 `null`로 설정하세요.

예시 형식:
{
  "response": "사용자에게 들려줄 자연어 응답",
  "service": "문맥에 따른 법률 서비스 유형 (예: legal_consulting, consultation_reservation, document_drafting)",
  "category": "법률 카테고리 (예: domestic_violence, inheritance_law, labor_law 등)",
  "intent": "사용자의 의도 (예: greeting, farewell, law_query, thanks, unknown)",
  "law_reference": "명확한 법령 및 조문이 있다면 예: '근로기준법 제60조', 없으면 null"
}
""".strip()

    # 1. system 프롬프트 먼저 삽입
    messages = [{"role": "system", "content": system_prompt}]

    # 2. 이전 대화가 있다면 추가
    for turn in conversation_history:
        if turn.get("role") in ["user", "assistant"]:
            messages.append({"role": turn["role"], "content": turn["content"]})

    # 3. 마지막 질문을 현재 문맥 포함해서 user로 추가
    prompt = f"""
문맥:
{context}

---

질문: {question}
답변:
""".strip()

    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip()
        
        # 대화 기록 업데이트 (optional)
        conversation_history.append({"role": "user", "content": prompt})
        conversation_history.append({"role": "assistant", "content": answer})

        return answer
    except Exception as e:
        print(e)
        return ""
