import pandas as pd
import numpy as np
import json
from gptbot.models import Embedding  # 모델 import
from openai import OpenAI
from typing import List
from scipy import spatial

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
    """문맥에 따라 질문에 답하는 기능"""

    df = load_embeddings_df()  # <== 이제 DB에서 임베딩을 불러옴

    context = create_context(question, df, max_len=200)
    prompt = f"""
당신은 친절하고 신뢰할 수 있는 법률 안내 챗봇(GPT)입니다. 
법률 정보, 법령, 법률 상담, 계약서 작성 등 법률적 질문에 대해 답변해 주세요.
모르겠거나 부족한 정보는 솔직히 "모르겠습니다"라고 답변합니다.
문맥:
{context}

---

질문: {question}
답변:
"""
    conversation_history.append({"role": "user", "content": prompt})

    try:
        # ChatGPT에서 답변 생성
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            temperature=1,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(e)
        return ""
