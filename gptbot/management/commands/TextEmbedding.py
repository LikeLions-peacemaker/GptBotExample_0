from django.core.management.base import BaseCommand
import pandas as pd
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
from gptbot.models import Embedding
import json
import os

class Command(BaseCommand):
    help = 'scraped.csv의 텍스트를 임베딩하고 DB에 저장합니다.'

    def handle(self, *args, **kwargs):
        load_dotenv()
        client = OpenAI()
        embedding_model = "text-embedding-3-small"
        embedding_encoding = "cl100k_base"
        max_tokens = 1500

        # 1. 데이터 로드 및 칼럼명 정리
        df = pd.read_csv("scraped.csv")  # manage.py 기준 경로
        df.columns = ['title', 'text']

        tokenizer = tiktoken.get_encoding(embedding_encoding)

        # 2. NaN/None 처리 및 모두 str로 변환, 토큰수 계산
        df['text'] = df['text'].fillna('').astype(str)
        df['n_tokens'] = df['text'].apply(lambda x: len(tokenizer.encode(x)))

        def split_into_many(text, max_tokens=500):
            sentences = text.split('.')
            n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]
            chunks = []
            tokens_so_far = 0
            chunk = []

            for sentence, token in zip(sentences, n_tokens):
                if tokens_so_far + token > max_tokens:
                    if chunk:
                        chunks.append(". ".join(chunk).strip() + ".")
                    chunk = []
                    tokens_so_far = 0
                if token > max_tokens:
                    continue
                chunk.append(sentence)
                tokens_so_far += token + 1
            if chunk:
                chunks.append(". ".join(chunk).strip() + ".")
            return chunks

        # 3. 최대 토큰수 넘는 텍스트 분할
        shortened = []
        for _, row in df.iterrows():
            text = row['text']
            n_token = row['n_tokens']
            if not text or text.strip() == "":
                continue
            if n_token > max_tokens:
                shortened += split_into_many(text)
            else:
                shortened.append(text)

        # 4. 새로운 DataFrame 생성, 토큰수 재계산
        df = pd.DataFrame(shortened, columns=['text'])
        df['text'] = df['text'].fillna('').astype(str)
        df['n_tokens'] = df['text'].apply(lambda x: len(tokenizer.encode(x)))

        # 5. 임베딩 함수 정의 (예외처리 포함)
        def get_embedding(text, model):
            text = text.replace("\n", " ")
            try:
                response = client.embeddings.create(input=[text], model=model)
                return response.data[0].embedding
            except Exception as e:
                print(f"임베딩 실패: {e}\n텍스트: {text[:50]}...")
                return None

        # 6. 임베딩 컬럼 추가
        df["embeddings"] = df.text.apply(lambda x: get_embedding(x, model=embedding_model))

        # 7. DB에 저장
        saved = 0
        for _, row in df.iterrows():
            text = row['text']
            embedding = row['embeddings']
            if embedding is None:
                continue
            Embedding.objects.create(
                text=text,
                embedding=json.dumps(embedding)
            )
            saved += 1
        self.stdout.write(self.style.SUCCESS(f"DB 저장 완료! ({saved}개)"))
