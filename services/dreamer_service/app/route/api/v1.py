from fastapi import APIRouter, HTTPException

from crud import dreamer_crud, dreamer_group_crud, dreamer_group_members_crud
from schemas import (NewDreamerRequest, NewDreamerResponse, UpdateDreamerRequest,
                     DreamerResponse, NewDreamerGroupRequest, NewDreamerGroupResponse, 
                     DreamerGroupResponse, UpdateDreamerGroupRequest, DreamerToGroupRequest, 
                     DreamerToGroupResponse,DreamerInGroup,DreamerGroupSummary)
from shared.utils.security import random_string
from shared.lib.API import Client
from models.DreamerTable import DreamerTableSchema
from models.DreamerGroupTable import DreamerGroupTableSchema
from models.DreamerGroupMembersTable import DreamerGroupMembersTableSchema


# /api/v1/dreamer
router = APIRouter()

# ================
# Dreamer Admin
# ================

@router.post("/admin/new", response_model=NewDreamerResponse)
async def create_dreamer(request: NewDreamerRequest):
    """新しいアカウントの作成"""
    _, result, error = dreamer_crud.create(DreamerTableSchema(**request.model_dump(), login_id = random_string()))
    print(error, flush=True)
    return NewDreamerResponse.model_validate(result)


@router.get("/admin/{login_id}", response_model=DreamerResponse)
async def get_dreamer(login_id: str):
    """dreamer情報の取得"""
    _, result, error = dreamer_crud.read(
        [
            ["login_id", "==", login_id]
        ] 
    )
    dreamer = result[0]
    
    # dreamerが所属するグループを取得
    _, members, error = dreamer_group_members_crud.read(
        [
            ["dreamer_id", "==", dreamer.dreamer_id]
        ]
    )
    print(error, flush=True)
    
    # グループ情報を取得
    groups = []
    if members:
        for member in members:
            _, group_result, error = dreamer_group_crud.read(
                [
                    ["group_id", "==", member.group_id]
                ]
            )
            if group_result:
                group = group_result[0]
                groups.append(DreamerGroupSummary(name=group.name, group_id=group.group_id))
    
    return DreamerResponse(
        dreamer_id=dreamer.dreamer_id,
        login_id=dreamer.login_id,
        organization_id=dreamer.organization_id,
        name_family=dreamer.name_family,
        name_given=dreamer.name_given,
        groups=groups
    )


@router.put("/admin/{dreamer_id}", response_model=DreamerResponse)
async def update_dreamer(dreamer_id: str, request: UpdateDreamerRequest):
    """dreamer情報の更新"""
    _, result, error=dreamer_crud.update(
        [
            ["dreamer_id", "==", dreamer_id]
        ], 
    request.model_dump(exclude_unset=True)
    )
    print(error, flush=True)
    return DreamerResponse.model_validate(result[0])


@router.delete("/admin/{dreamer_id}", response_model=DreamerResponse)
async def delete_dreamer(dreamer_id: str):
    """dreamer情報の削除"""
    # 所属している全グループから削除
    _, _, error = dreamer_group_members_crud.delete(
        [
            ["dreamer_id", "==", dreamer_id]
        ]
    )
    print(error, flush=True)
    
    # dreamerを削除
    _, result, error=dreamer_crud.delete(
        [
            ["dreamer_id", "==", dreamer_id]
        ]
    )
    print(error, flush=True)
    if not result:
        raise HTTPException(status_code=404, detail="dreamer が見つかりません")
    return DreamerResponse.model_validate(result[0])

# ================
# Dreamer Groups
# ================

@router.post("/groups/new", response_model=NewDreamerGroupResponse)
async def create_group(request: NewDreamerGroupRequest):
    """新しいグループの作成"""
    # メンバーに指定された dreamer_id を事前に全件確認（存在しなければ 400）
    for dreamer_id in request.dreamers:
        _, dreamer_result, error = dreamer_crud.read(
            [["dreamer_id", "==", dreamer_id]]
        )
        if not dreamer_result:
            raise HTTPException(status_code=400, detail="dreamer_id が存在しません")

    group_data = request.model_dump(exclude={"dreamers"})
    group_instance = DreamerGroupTableSchema(**group_data)

    _, group_result, error = dreamer_group_crud.create(group_instance)
    
    print(error, flush=True)
    group_id = group_result.group_id

    # メンバー登録
    added_dreamers = []
    for dreamer_id in request.dreamers:
        member_instance = DreamerGroupMembersTableSchema(
            group_id=group_id,
            dreamer_id=dreamer_id
        )
        _, member_result, error = dreamer_group_members_crud.create(member_instance)
        print(error, flush=True)
        added_dreamers.append(member_result)

    return NewDreamerGroupResponse.model_validate(group_result)


@router.get("/groups/{group_id}", response_model=DreamerGroupResponse)
async def get_group(group_id: str):
    """グループ情報の取得"""
    _, group_result, error = dreamer_group_crud.read(
        [
            ["group_id", "==", group_id]
        ]
    )
    print(error, flush=True)

    group = group_result[0]
    _, members, error = dreamer_group_members_crud.read(
        [
            ["group_id", "==", group_id]
        ]
    )
    print(error, flush=True)
    
    # 各メンバーのdreamer情報を取得
    dreamers = []
    if members:
        for member in members:
            _, dreamer_result, error = dreamer_crud.read(
                [
                    ["dreamer_id", "==", member.dreamer_id]
                ]
            )
            if dreamer_result:
                dreamer = dreamer_result[0]
                full_name = f"{dreamer.name_family} {dreamer.name_given}"
                dreamers.append(DreamerInGroup(name=full_name, dreamer_id=dreamer.dreamer_id))
        
    return DreamerGroupResponse(
        name=group.name,
        description=group.description,
        dreamers=dreamers
    )


@router.put("/groups/{group_id}", response_model=DreamerGroupResponse)
async def update_group(group_id: str, request: UpdateDreamerGroupRequest):
    """グループ情報の更新"""
    _, result, error=dreamer_group_crud.update(
        [
            ["group_id", "==", group_id]
        ],
        request.model_dump(exclude_unset=True)
    )
    print(error, flush=True)
    return DreamerGroupResponse.model_validate(result[0])


@router.delete("/groups/{group_id}", response_model=DreamerGroupResponse)
async def delete_group(group_id: str):
    """グループを削除"""
    # グループのメンバーを全て削除
    _, _, error = dreamer_group_members_crud.delete(
        [
            ["group_id", "==", group_id]
        ]
    )
    print(error, flush=True)
    
    # グループを削除
    _, result, error = dreamer_group_crud.delete(
        [
            ["group_id", "==", group_id]
        ]
    )
    print(error, flush=True)
    return DreamerGroupResponse.model_validate(result[0])

#================
# Dreamer Group Members
#================

@router.put("/groups/{group_id}/add_dreamer", response_model=DreamerToGroupResponse)
async def add_dreamer_to_group(group_id: str, request: DreamerToGroupRequest):
    """グループにdreamerを追加"""
    # グループの存在確認
    _, group_result, error = dreamer_group_crud.read(
        [["group_id", "==", group_id]]
    )
    if not group_result:
        raise HTTPException(status_code=404, detail="group が見つかりません")

    # 追加対象 dreamer_id を事前に全件確認（外部キー違反防止）
    for dreamer_id in request.dreamers:
        _, dreamer_result, error = dreamer_crud.read(
            [["dreamer_id", "==", dreamer_id]]
        )
        if not dreamer_result:
            raise HTTPException(status_code=400, detail="dreamer_id が存在しません")

    added_dreamers = []

    for dreamer_id in request.dreamers:
        member_instance = DreamerGroupMembersTableSchema(
            group_id=group_id,
            dreamer_id=dreamer_id
        )
        _, member_result, error = dreamer_group_members_crud.create(member_instance)
        print(error, flush=True)
        added_dreamers.append(member_result)

    dreamer_ids = [member.dreamer_id for member in added_dreamers]
    return DreamerToGroupResponse.model_validate({"dreamers": dreamer_ids})


@router.delete("/groups/{group_id}/remove_dreamer", response_model=DreamerToGroupResponse)
async def remove_dreamer_from_group(group_id: str, request: DreamerToGroupRequest):
    """グループからdreamerを削除"""
    deleted_ids = []

    for dreamer_id in request.dreamers:
        _, result, error = dreamer_group_members_crud.delete(
            [
                ["group_id", "==", group_id],
                ["dreamer_id", "==", dreamer_id]
            ]
        )
        print(error, flush=True)
        if result:
            deleted_ids.append(dreamer_id)
    return DreamerToGroupResponse.model_validate({"dreamers": deleted_ids})

# ================
# Init Questions / Answers
# ================

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

INIT_QUESTIONS = [
    {
        "category": "Category 1: 認知・思考スタイル (脳のクセ)",
        "questions": [
            {"q": "新しい複雑な機械やソフトを目の前にしました。まずどうしますか？", "opts": ["説明書を最初から最後まで熟読し、構造を理解する", "とりあえず触って動かしながら、体で覚える", "詳しい人に使い方を聞くか、解説動画を見る", "仕組みはどうでもいいので、必要な機能だけ覚える", "分解して中身がどうなっているか見たくなる"]},
            {"q": "議論において、あなたが最も重視することは？", "opts": ["論理的な整合性と、エビデンス（証拠）の有無", "参加者全員が納得しているかどうかの「空気」", "これまでにない新しい視点やアイデアが出るかどうか", "最終的に具体的なアクションプランが決まるかどうか", "そもそも議論は嫌い。一人で考えたい"]},
            {"q": "あなたの記憶の仕方に最も近いのは？", "opts": ["映像や写真のように「絵」で覚えている", "言葉や文章、物語の「文脈」で覚えている", "その時の感情や、身体の感覚で覚えている", "年号や数値などの「データ」で覚えている", "物事の関連性や体系的な「構造」で覚えている"]},
            {"q": "単純作業（データ入力や検品など）を長時間続けることについて。", "opts": ["苦ではない。むしろ無心になれて好き", "音楽などを聴きながらならできる", "正確にやる自信はあるが、すぐに飽きる", "絶対に無理。5分で発狂しそうになる", "効率化する方法を考えることに夢中になる"]},
            {"q": "「未解決の難問」に対してどう感じますか？", "opts": ["燃える。何としても解き明かしたい", "不安になる。早く正解を知りたい", "ワクワクするが、自分一人では荷が重い", "興味がない。誰かが解決すればいい", "そもそも「正解」なんてないと思う"]},
            {"q": "アイデアを出すときのアプローチは？", "opts": ["既存の要素を組み合わせて、論理的に導く", "散歩中などに突然「降ってくる」のを待つ", "ノートに書き出しながら、カオスな思考を整理する", "他人と雑談しながら、刺激を受けて広げる", "過去の成功事例を徹底的にリサーチして模倣する"]},
        ]
    },
    {
        "category": "Category 2: 対人・コミュニケーション (心の距離)",
        "questions": [
            {"q": "パーティーや交流会でのあなたの振る舞いは？", "opts": ["中心になって場を盛り上げ、多くの人と話す", "少数の知人と深い話をして過ごす", "人間観察に徹し、自分からは話しかけない", "義務感で参加するが、早く帰りたい", "ビジネスチャンスを探して、名刺交換に奔走する"]},
            {"q": "誰かがミスをして落ち込んでいます。どう声をかけますか？", "opts": ["「次はこうすればいいよ」と具体的な解決策を示す", "「大変だったね」と感情に寄り添い、話を聞く", "あえて何も言わず、いつも通りに接する", "原因を分析し、再発防止策を厳しく問う", "気分転換に食事や遊びに誘う"]},
            {"q": "リーダーという役割についてどう思いますか？", "opts": ["自分から進んでやりたい。決定権を持ちたい", "頼まれればやるが、本音はNo.2が楽", "絶対にやりたくない。責任を負いたくない", "肩書きだけのリーダーなら興味がない", "影のリーダーとして、実質的な支配権を持ちたい"]},
            {"q": "「説得」や「交渉」の場面において。", "opts": ["得意。論理と情熱で相手を動かす自信がある", "相手の顔色を伺ってしまい、譲歩しがち", "苦手。対立するくらいなら自分が我慢する", "詐欺師になれるレベルで得意", "データだけ提示して、判断は相手に委ねる"]},
            {"q": "仕事仲間との理想的な距離感は？", "opts": ["家族のように仲良く、プライベートも共有したい", "仕事中は協力するが、プライベートは別", "完全にドライな関係。業務連絡以外は不要", "ライバルとして切磋琢磨する緊張感が欲しい", "師弟関係のように、尊敬できる人と付き合いたい"]},
            {"q": "人前でプレゼンテーションをする機会がありました。", "opts": ["最高に目立てるチャンス。緊張より興奮が勝る", "しっかり準備すれば問題ない。淡々とこなす", "極度の緊張で、できれば仮病を使って休みたい", "聴衆の反応を見ながらアドリブで話すのが好き", "資料作りは好きだが、発表は誰かに任せたい"]},
        ]
    },
    {
        "category": "Category 3: 行動特性・スキル (手と足)",
        "questions": [
            {"q": "「手先の器用さ」を100点満点で自己採点すると？", "opts": ["90-100点（極めて器用。ミリ単位の作業が好き）", "70-89点（平均より上。DIYや料理は得意）", "50-69点（普通。日常困ることはない）", "30-49点（やや不器用。細かい作業はイライラする）", "0-29点（絶望的。よく物を壊す）"]},
            {"q": "デジタルデバイス（PC/スマホ）との関係性は？", "opts": ["身体の一部。一日中画面を見ていても平気", "便利な道具として使いこなしている", "必要最低限しか使いたくない", "苦手。アナログな手帳や紙の方が信頼できる", "プログラミングや改造をするレベルで好き"]},
            {"q": "じっとしているのと、動き回るの、どちらが楽？", "opts": ["デスクに座って一日中動かないのが一番楽", "座りっぱなしは苦痛。適度に動きたい", "外に出て、常に移動している方が活力が湧く", "肉体を極限まで使うような重労働が好き", "場所にとらわれず、ノマド的に働きたい"]},
            {"q": "マルチタスク（同時並行作業）について。", "opts": ["得意。複数の皿を回すような状況に燃える", "できるが、質は落ちる気がする", "苦手。一つ終わらせてから次に行きたい", "パニックになる。シングルタスクしか無理", "他人に仕事を振るのが得意なので問題ない"]},
            {"q": "リスクや不確実性に対するスタンスは？", "opts": ["ハイリスク・ハイリターンが好き。スリルが欲しい", "計算できるリスクなら取る。成長には必要", "石橋を叩いて渡る。安全性・確実性が最優先", "変化を嫌う。昨日と同じ今日がいい", "リスク管理のプロ。他人のリスクを減らしたい"]},
            {"q": "マニュアル（手順書）への対応は？", "opts": ["一言一句守る。それが一番効率的で安全", "基本は守るが、自分なりにアレンジを加える", "マニュアルは無視して、自己流で最速を目指す", "そもそもマニュアルがない状況を作るのが好き", "マニュアルを作る側に回りたい"]},
        ]
    },
    {
        "category": "Category 4: 環境・感覚 (五感の好み)",
        "questions": [
            {"q": "理想的な職場の「音」環境は？", "opts": ["完全な静寂。時計の針の音も気になる", "カフェのような適度な雑音やBGMが欲しい", "活気ある話し声や電話の音が飛び交う場所", "機械音や工事音が鳴り響く、パワーのある場所", "自然の音（風、波、鳥の声）が聞こえる場所"]},
            {"q": "理想的な職場の「視覚」環境は？", "opts": ["整理整頓された、無機質で清潔なオフィス", "好きなフィギュアや植物に囲まれた自分だけの城", "雑多だが、クリエイティブな刺激に満ちたアトリエ", "常に景色が変わる、車窓や屋外", "薄暗くて狭い、没頭できる秘密基地のような場所"]},
            {"q": "勤務時間とリズムについて。", "opts": ["9時-17時できっちり定時。ルーチンが心地よい", "フレックス制で、朝型・夜型を自由に選びたい", "プロジェクト単位で、短期間に集中して後は休みたい", "24時間365日、仕事とプライベートの境目をなくしたい", "週3日だけ働き、残りは趣味に生きたい"]},
            {"q": "服装や身だしなみについて。", "opts": ["スーツや制服でビシッと決めたい（ON/OFF切替）", "オフィスカジュアル程度が楽", "完全に自由。Tシャツ短パンで働きたい", "汚れてもいい作業着が一番落ち着く", "自分のセンスを表現できるファッションが良い"]},
            {"q": "匂いや空気感について。", "opts": ["無臭で、空調が完璧に管理された部屋", "コーヒーやアロマの香りがするリラックス空間", "土、木、油、インクなどの「現場の匂い」が好き", "消毒液の匂いがするような、清潔第一の空間", "外気を感じられる開放的な空間"]},
            {"q": "「変化」と「安定」のバランスは？", "opts": ["100%安定。予測可能な未来が欲しい", "基本は安定だが、たまにイベントが欲しい", "半々くらい。ルーチンと新規案件のバランス", "毎日違うことが起きる刺激的な日々が良い", "カオス（混沌）こそが我が家。安定は退屈"]},
        ]
    },
    {
        "category": "Category 5: 価値観・報酬 (魂の充足)",
        "questions": [
            {"q": "仕事を通じて最も得たいものは？", "opts": ["高い収入と経済的自由", "社会的な地位と他者からの尊敬", "自分の成長と専門性の向上", "世の中への貢献と社会的意義", "人との繋がりと所属感"]},
            {"q": "理想のキャリアの終着点は？", "opts": ["業界のトップに君臨する経営者", "特定分野で世界的に知られる専門家", "愛する家族と豊かな生活を送れる状態", "自分のビジョンを実現した起業家", "後進を育て、社会に影響を与えた教育者"]},
            {"q": "「失敗」に対するあなたのスタンスは？", "opts": ["失敗は絶対に避けたい。完璧主義者だ", "失敗は糧。むしろ積極的に挑戦して失敗したい", "小さな失敗は許容するが、大きな失敗は怖い", "失敗の原因を徹底的に分析して再発防止に努める", "失敗しても誰かのせいにしてしまう傾向がある"]},
            {"q": "「お金」と「やりがい」どちらを優先する？", "opts": ["完全にお金。生活が安定してこそ仕事ができる", "やりがいが最優先。お金は後からついてくる", "両方が高いレベルで両立している仕事が理想", "今はやりがい、将来はお金のバランスを変えたい", "どちらでもない。とにかく楽な仕事がいい"]},
            {"q": "あなたが最も嫌いな職場環境は？", "opts": ["成果を正当に評価されない、不公平な環境", "変化がなく、毎日同じルーティンを繰り返す場所", "人間関係が複雑で、派閥や根回しが必要な場所", "自分の意見を言えない、トップダウンの独裁環境", "チームワークがなく、孤独に作業し続ける環境"]},
            {"q": "10年後の自分に最も近いイメージは？", "opts": ["大企業の役員として、組織を率いている", "フリーランスや個人事業主として、自由に働いている", "専門資格を持つプロフェッショナルとして活躍している", "自分で会社を立ち上げ、チームを持っている", "海外を拠点に、グローバルに活動している"]},
        ]
    },
]


# question_id → (category, q, opts) の逆引きマップを事前に構築
_QUESTION_MAP: Dict[str, Any] = {}
_order = 1
for _cat in INIT_QUESTIONS:
    for _q in _cat["questions"]:
        _QUESTION_MAP[f"q{_order}"] = {"category": _cat["category"], "q": _q["q"], "opts": _q["opts"]}
        _order += 1


class InitAnswerItem(BaseModel):
    question_id: str
    option_id: str
    question_version: int

class InitAnswersRequest(BaseModel):
    answers: List[InitAnswerItem]


@router.get("/init-questions")
async def get_init_questions():
    """初期診断質問の取得（フロント互換形式）"""
    questions = []
    order = 1
    for cat in INIT_QUESTIONS:
        for q_item in cat["questions"]:
            questions.append({
                "question_id": f"q{order}",
                "category": cat["category"],
                "question_text": q_item["q"],
                "question_order": order,
                "version": 1,
                "options": [
                    {"option_id": f"q{order}_o{i+1}", "option_text": opt, "option_order": i+1}
                    for i, opt in enumerate(q_item["opts"])
                ]
            })
            order += 1
    return {"questions": questions, "version": 1, "total_questions": len(questions)}


@router.post("/init-answers")
async def post_init_answers(request: InitAnswersRequest, dreamer_id: str = ""):
    """初期診断回答の受け取り（job serviceに転送してレコメンド生成）"""
    import httpx

    # question_id + option_id → テキストに変換して job service へ送る
    answers_for_job = []
    for item in request.answers:
        q_info = _QUESTION_MAP.get(item.question_id)
        if not q_info:
            continue
        # option_id は "q{n}_o{m}" 形式。m-1 でインデックスに変換
        try:
            opt_idx = int(item.option_id.split("_o")[-1]) - 1
            answer_text = q_info["opts"][opt_idx]
        except Exception:
            answer_text = item.option_id
        answers_for_job.append({
            "category": q_info["category"],
            "q": q_info["q"],
            "a": answer_text,
        })

    payload = {
        "dreamer_id": dreamer_id or "anonymous",
        "answers": answers_for_job,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "http://job-service:8000/api/v1/analyze",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"job-service への転送に失敗: {str(e)}")
