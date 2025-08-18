"""
간단한 춘천시 웹 챗봇 - 기본 버전
Simple Chuncheon Web Chatbot - Basic Version
"""

from flask import Flask, render_template_string, request, jsonify
import os
import requests

app = Flask(__name__)

# HTML 템플릿 (인라인으로 포함)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>춘천시 AI 가이드 춘이 🌸</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Malgun Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .chat-area {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            border-bottom: 1px solid #eee;
        }

        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
        }

        .user-message {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }

        .bot-message {
            background: #f1f3f4;
            color: #333;
        }

        .input-area {
            padding: 20px;
            display: flex;
            gap: 10px;
        }

        .input-field {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
        }

        .input-field:focus {
            border-color: #667eea;
        }

        .send-btn {
            padding: 15px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
        }

        .send-btn:hover {
            background: #5a6fd8;
        }

        .quick-questions {
            padding: 20px;
            border-top: 1px solid #eee;
            background: #f9f9f9;
        }

        .quick-questions h3 {
            margin-bottom: 15px;
            color: #333;
        }

        .quick-btn {
            display: inline-block;
            margin: 5px;
            padding: 8px 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
        }

        .quick-btn:hover {
            background: #5a6fd8;
        }

        .loading {
            color: #667eea;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌸 춘천시 AI 가이드 춘이</h1>
            <p>강원특별자치도 춘천시의 모든 정보를 안내해드립니다</p>
        </div>

        <div class="chat-area" id="chatArea">
            <div class="message bot-message">
                <strong>🌸 춘이:</strong> 안녕하세요~ 춘천 사는 춘이에요!<br>
                춘천 놀러오셨어요? 뭐든 물어보세요~ 제가 아는 건 다 알려드릴게요 ㅎㅎ 😊
            </div>
        </div>

        <div class="input-area">
            <input type="text" id="messageInput" class="input-field" placeholder="춘천에 대해 궁금한 것을 물어보세요..." maxlength="200">
            <button id="sendBtn" class="send-btn">전송</button>
        </div>

        <div class="quick-questions">
            <h3>🚀 빠른 질문</h3>
            <button class="quick-btn" onclick="askQuestion('춘천 닭갈비 맛집 추천해줘')">🍗 닭갈비 맛집</button>
            <button class="quick-btn" onclick="askQuestion('남이섬 가는 방법 알려줘')">🏝️ 남이섬 가는 방법</button>
            <button class="quick-btn" onclick="askQuestion('춘천 날씨 어때?')">🌤️ 춘천 날씨</button>
            <button class="quick-btn" onclick="askQuestion('춘천역 연락처는?')">🚂 춘천역 정보</button>
            <button class="quick-btn" onclick="askQuestion('막국수 체험할 수 있는 곳')">🍜 막국수 체험</button>
            <button class="quick-btn" onclick="askQuestion('춘천 축제 일정 알려줘')">🌸 축제 정보</button>
        </div>
    </div>

    <script>
        const chatArea = document.getElementById('chatArea');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.innerHTML = isUser ? 
                `<strong>👤 사용자:</strong> ${content}` : 
                `<strong>🌸 춘이:</strong> ${content}`;
            
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function askQuestion(question) {
            messageInput.value = question;
            sendMessage();
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage(message, true);
            messageInput.value = '';
            sendBtn.disabled = true;

            // 로딩 메시지
            addMessage('<span class="loading">답변을 준비하고 있어요... 🤔</span>');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                
                // 로딩 메시지 제거
                chatArea.removeChild(chatArea.lastChild);
                
                if (data.success) {
                    addMessage(data.message);
                } else {
                    addMessage('죄송합니다. 오류가 발생했습니다: ' + data.message);
                }
            } catch (error) {
                // 로딩 메시지 제거
                chatArea.removeChild(chatArea.lastChild);
                addMessage('네트워크 오류가 발생했습니다. 다시 시도해주세요.');
            } finally {
                sendBtn.disabled = false;
            }
        }

        // 이벤트 리스너
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

# 춘천시 기본 정보 (API 없이도 동작하도록)
CHUNCHEON_INFO = {
    "닭갈비": {
        "맛집": ["춘천닭갈비골목 (033-252-9995)", "춘천명동닭갈비 (033-253-6600)"],
        "설명": "춘천의 대표 음식으로 매콤달콤한 양념에 볶은 닭고기 요리입니다."
    },
    "남이섬": {
        "연락처": "031-580-8114",
        "주소": "강원특별자치도 춘천시 남산면 남이섬길 1",
        "설명": "춘천의 대표 관광명소로 아름다운 자연경관을 자랑합니다."
    },
    "춘천역": {
        "연락처": "1544-7788",
        "주소": "강원특별자치도 춘천시 근화동 472-1",
        "설명": "춘천의 주요 기차역으로 서울과 연결되는 교통 거점입니다."
    },
    "막국수": {
        "체험장소": "막국수체험박물관 (033-244-8869)",
        "주소": "강원특별자치도 춘천시 신북읍 신샘밭로 264",
        "설명": "춘천의 대표 음식인 막국수를 직접 만들어볼 수 있습니다."
    }
}

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """채팅 API 엔드포인트"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower()
        
        if not user_message.strip():
            return jsonify({
                'success': False,
                'message': '질문을 입력해주세요!'
            })
        
        # 간단한 키워드 기반 응답
        response = """음... 그건 잘 모르겠는데요 😅
        
혹시 이런 거 물어보시려던 건가요?
• 춘천 맛집이나 관광지
• 교통편 정보
• 축제나 행사 일정
• 날씨 정보

다시 한번 물어봐주세요~ 제가 도와드릴게요!"""
        
        if "닭갈비" in user_message or "맛집" in user_message:
            info = CHUNCHEON_INFO["닭갈비"]
            response = f"""아~ 닭갈비요! 🍗 진짜 춘천 오면 무조건 먹어야죠 ㅋㅋ

저는 보통 친구들 오면 여기 데려가요:
• {info['맛집'][0]} - 여기 진짜 현지인들 많이 가요
• {info['맛집'][1]} - 관광객들한테도 인기 짱!

참고로 우동사리 꼭 추가하세요! 그리고 마지막에 볶음밥도 필수에요~
배 터질 수도 있으니까 점심 굶고 가시는 거 추천 ㅎㅎ 😋"""

        elif "남이섬" in user_message:
            info = CHUNCHEON_INFO["남이섬"]
            response = f"""남이섬이요? 🏝️ 아 거기 진짜 예뻐요!

특히 가을에 메타세콰이아길 걸으면... 와 대박이에요 진짜.
겨울연가 촬영지라서 외국인들도 엄청 많이 와요!

📞 문의: {info['연락처']}
📍 위치: {info['주소']}

춘천역에서 가실 거면 버스 타고 가세요~ 택시는 좀 비싸더라구요.
아! 그리고 자전거 빌려서 섬 한바퀴 도는 것도 완전 추천! 🚴‍♂️"""

        elif "춘천역" in user_message or "연락처" in user_message:
            info = CHUNCHEON_INFO["춘천역"]
            response = f"""춘천역 정보 찾으시는군요! 🚂

📞 대표번호: {info['연락처']}
📍 위치: {info['주소']}

ITX-청춘 타면 서울에서 딱 1시간이에요! 엄청 빠르죠?
주말엔 사람 많으니까 미리 예매하는 게 좋아요~

역 앞에 춘천명물거리도 있으니까 시간 있으면 둘러보세요! 🚄"""

        elif "막국수" in user_message or "체험" in user_message:
            info = CHUNCHEON_INFO["막국수"]
            response = f"""막국수 체험이요? 오~ 재밌어요! 🍜

{info['체험장소']}에서 할 수 있어요!
📍 주소: {info['주소']}

아이들이랑 가기 진짜 좋고요, 직접 만들어서 먹으니까 더 맛있더라구요 ㅎㅎ
체험 끝나고 바로 먹을 수 있어서 점심 해결도 되고 일석이조! 👨‍🍳

여름에 가면 시원하게 먹을 수 있어서 더 좋아요~"""

        elif "날씨" in user_message:
            response = """춘천 날씨요? 🌤️

실시간은 네이버나 기상청 봐야 정확한데요~

근데 춘천이 진짜 사계절이 확실해요!
• 봄엔 벚꽃 미쳤고요 🌸 (4월 초중순 진짜 예뻐요)
• 여름엔 의암호 물놀이 최고! 🏊‍♂️ (근데 좀 더워요 ㅠ)
• 가을엔 단풍 구경 가야죠 🍁 (10월 말이 딱!)
• 겨울엔... 어우 춥긴 한데 눈 오면 진짜 이뻐요 ❄️

참고로 일교차 심하니까 가디건 챙기세요!"""

        elif "축제" in user_message:
            response = """축제 정보요? 춘천 축제 진짜 많아요! 🎉

제가 추천하는 거:
• 4월에 **벚꽃축제** - 삼천동 벚꽃길 진짜... 말이 안 나와요 🌸
• 5월 **마임축제** - 세계 각국 마임 배우들 와서 공연해요! 신기함
• 여름엔 **물레길축제** - 의암호에서 수상스키도 타고 재밌어요
• 8-9월 **닭갈비축제** - 이때 가면 닭갈비 싸게 먹을 수 있어요 ㅋㅋ

정확한 날짜는 매년 조금씩 바뀌니까
춘천시청(033-250-3000) 전화하거나 홈페이지 확인해보세요! 📞"""

        elif "안녕" in user_message or "처음" in user_message:
            response = """안녕하세요~ 춘천 가이드 춘이에요! 🌸

춘천 놀러오셨어요? 아니면 정보 찾으시는 거예요?
뭐든 물어보세요! 제가 아는 건 다 알려드릴게요 ㅎㅎ

• 닭갈비 맛집 🍗 (진짜 맛집만 알려드림)
• 남이섬 가는법 🏝️ (꿀팁도 있음)  
• 막국수 체험 🍜 (애들이랑 가기 좋아요)
• 버스, 기차 정보 🚂
• 축제 일정 🎉
• 날씨나 뭐 기타등등...

편하게 물어보세요~ 😊"""

        return jsonify({
            'success': True,
            'message': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        })

if __name__ == '__main__':
    print("🌸 춘천시 AI 가이드 춘이 웹 서버를 시작합니다!")
    print("📱 브라우저에서 http://localhost:8080 으로 접속하세요!")
    app.run(debug=True, host='0.0.0.0', port=8080)
