import traceback

from flask import Flask, jsonify, render_template, request

from ai import analyze_answer, generate_question


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/interview")
def interview():
    return render_template("interview.html")


@app.route("/get_question", methods=["POST"])
def get_question():
    try:
        data = request.get_json(silent=True) or {}

        interview_type = data.get("type", "")
        personality = data.get("personality", "")
        history = data.get("history", [])

        # historyが想定外の形式でも落ちないようにする
        if not isinstance(history, list):
            history = []

        # 空文字を除き、直近12問だけ使う
        history = [
            str(item).strip()
            for item in history
            if str(item).strip()
        ][-12:]

        print("受信した面接種類:", interview_type)
        print("受信した面接官タイプ:", personality)
        print("過去質問数:", len(history))

        question = generate_question(
            interview_type,
            personality,
            history
        )

        print("生成された質問:")
        print(question)
        print("質問のデータ型:", type(question))

        if not question:
            raise ValueError("質問が生成されませんでした。")

        return jsonify({
            "question": str(question)
        })

    except Exception as e:
        print("========== get_question エラー ==========")
        print("エラーの種類:", type(e).__name__)
        print("エラー内容:", e)
        traceback.print_exc()
        print("=========================================")

        return jsonify({
            "question": "質問の生成中にエラーが発生しました。",
            "error": str(e)
        }), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    answer = ""

    try:
        data = request.get_json(silent=True) or {}

        question = data.get("question", "")
        answer = data.get("answer", "")

        print("分析対象の質問:")
        print(question)

        print("分析対象の回答:")
        print(answer)

        if not question:
            raise ValueError("質問が送信されていません。")

        if not answer.strip():
            raise ValueError("回答が入力されていません。")

        result = analyze_answer(
            question,
            answer
        )

        print("Geminiの分析結果:")
        print(result)
        print("分析結果のデータ型:", type(result))

        if not isinstance(result, dict):
            raise TypeError(
                f"analyze_answerの戻り値が辞書ではありません。"
                f"現在の型: {type(result).__name__}"
            )

        return jsonify({
            "corrected_answer": result.get(
                "corrected_answer",
                answer
            ),
            "score": result.get("score", 0),
            "good": result.get("good", ""),
            "improve": result.get("improve", ""),
            "follow": result.get("follow", "")
        })

    except Exception as e:
        print("========== analyze エラー ==========")
        print("エラーの種類:", type(e).__name__)
        print("エラー内容:", e)
        traceback.print_exc()
        print("=====================================")

        return jsonify({
            "corrected_answer": answer,
            "score": 0,
            "good": "分析中にエラーが発生しました。",
            "improve": "通信またはAI処理を確認してください。",
            "follow": "",
            "error": str(e)
        }), 500


@app.route("/result")
def result():
    return render_template("result.html")


if __name__ == "__main__":
    app.run(debug=True)
