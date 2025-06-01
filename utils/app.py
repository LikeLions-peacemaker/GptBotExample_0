from search import answer_question

# 초기 대화 기록 설정
conversation_history = [{"role": "system", "content": "hi"}]

def chat():
    while True:
        # 사용자로부터 입력 받기
        user_input = input("User: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chat.")
            break

        if user_input:
            # 사용자의 질문을 대화 기록에 추가
            conversation_history.append({"role": "user", "content": user_input})
            
            # answer_question 함수를 사용해 응답을 생성
            answer = answer_question(user_input, conversation_history)

            # 생성된 응답을 대화 기록에 추가
            conversation_history.append({"role": "assistant", "content": answer})
            
            # 응답을 콘솔에 출력
            print(f"Assistant: {answer}")
        else:
            print("Error: No message provided. Please try again.")

if __name__ == '__main__':
    print("Chatbot is running. Type 'exit' or 'quit' to end the chat.")
    chat()
