import json

from google import genai

from config import GEMINI_API_KEY


MODEL_NAME = "gemini-3.5-flash"


def get_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEYが設定されていません (.env確認)")

    return genai.Client(api_key=GEMINI_API_KEY)


def generate_question(interview_type, personality, history=None):
    client = get_client()

    history = history or []

    if history:
        history_text = "\n".join(
            f"{i + 1}. {question}"
            for i, question in enumerate(history)
        )
    else:
        history_text = "なし"

    prompt = f"""
あなたは高校生向けの面接官です。
実際の進学面接・就職面接を想定し、高校生が練習しやすい質問を1つだけ作ってください。

【面接種類】
{interview_type}

【面接官タイプ】
{personality}

【この面接練習ですでに出した質問】
{history_text}

次のルールを必ず守ってください。

・過去に出した質問と同じ質問は出さない
・言い換えただけの、意味がほぼ同じ質問も出さない
・質問テーマができるだけ連続しないようにする
・「高校生活で頑張ったこと」「高校生活で楽しかったこと」など、学校生活の思い出系に偏らない
・同じセッションで「頑張ったこと／楽しかったこと／印象に残ったこと」系は原則1回までにする
・高校生が30秒～2分程度で答えられる質問にする
・質問は一度に1つだけにする
・長い前置きや挨拶は不要
・Markdownの太字（**）などの装飾を使わない
・質問文だけを返す

質問テーマの例：
志望理由、長所、短所、自己PR、資格、部活動、委員会活動、友人関係、
失敗経験、困難への対処、協力した経験、責任感、将来の目標、
入学後・入社後に取り組みたいこと、最近関心を持ったこと、
苦手なことへの向き合い方、周囲からどんな人と言われるか、
学校・企業を選んだ理由、社会人として大切だと思うこと。

過去質問を見て、まだ十分に聞いていないテーマを優先してください。
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Geminiから質問文が返りませんでした。")

    return response.text.strip()


def analyze_answer(question, answer):
    client = get_client()

    prompt = f"""
あなたは高校生の面接練習を支援する面接官です。

以下の質問と生徒の回答を確認してください。

【質問】
{question}

【生徒の回答】
{answer}

最初に、生徒の回答に含まれる明らかな誤字・脱字・
音声認識による変換ミスだけを修正してください。

例：
「死亡動機」→「志望動機」
「高校でがんばりましだ」→「高校で頑張りました」

ただし、以下を必ず守ってください。

・生徒が話していない内容を追加しない
・回答を模範回答に作り直さない
・文章量を増やさない
・回答の意味を変えない
・明らかな誤認識だけを修正する
・修正する必要がなければ原文をそのまま使用する

そのうえで、面接回答として評価してください。

100点満点で採点し、
・良かった点
・改善点
を高校生にも分かりやすく説明してください。

必ず以下のJSON形式だけで回答してください。
説明文やMarkdown（```）は不要です。

{{
    "corrected_answer": "誤字等を修正した回答",
    "score": 80,
    "good": "良かった点",
    "improve": "改善点",
    "follow": ""
}}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Geminiから分析結果が返りませんでした。")

    text = response.text.strip()

    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Geminiの分析結果をJSONとして読み取れませんでした: {text}"
        ) from e

    if not isinstance(data, dict):
        raise ValueError("Geminiの分析結果がJSONオブジェクトではありません。")

    return data
