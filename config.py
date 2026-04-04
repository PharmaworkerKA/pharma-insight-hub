"""PharmaPedia Japan - サイト設定"""

SITE_NAME = "PharmaPedia Japan"
SITE_TAGLINE = "製薬・臨床開発の総合メディア"
SITE_DESCRIPTION = (
    "CDISC、FDA規制、臨床統計、ファーマコビジランス、製薬DXの最新情報を毎日配信。"
    "製薬・臨床開発のプロフェッショナルのための総合ナレッジベース。"
)
SITE_URL = "https://pharmaworkerka.github.io/pharma-insight-hub"
SITE_LANGUAGE = "ja"
GITHUB_REPO = "PharmaworkerKA/pharma-insight-hub"

# YouTube（将来的に追加）
YOUTUBE_CHANNEL_URL = ""
YOUTUBE_CHANNEL_NAME = "PharmaPedia Japan"

# Google Analytics
GOOGLE_ANALYTICS_ID = ""

# 各ブログの設定
BLOGS = [
    {
        "name": "CDISC Standards Navigator",
        "short_name": "CDISC",
        "url": "https://pharmaworkerka.github.io/cdisc-navigator",
        "feed_url": "https://pharmaworkerka.github.io/cdisc-navigator/feed.xml",
        "description": "SDTM・ADaM・Define-XMLなどCDISC標準規格の実践ガイド",
        "category": "CDISC・データ標準",
        "icon": "📊",
        "color": "#2563eb",
    },
    {
        "name": "GCP実務ナビ",
        "short_name": "GCP",
        "url": "https://pharmaworkerka.github.io/gcp-navi",
        "feed_url": "https://pharmaworkerka.github.io/gcp-navi/feed.xml",
        "description": "ICH-GCP E6(R3)・臨床試験実施基準の実務ノウハウ",
        "category": "GCP・治験実務",
        "icon": "🏥",
        "color": "#0d9488",
    },
    {
        "name": "FDA規制インサイト",
        "short_name": "FDA",
        "url": "https://pharmaworkerka.github.io/fda-insight",
        "feed_url": "https://pharmaworkerka.github.io/fda-insight/feed.xml",
        "description": "FDA規制動向・ガイダンス・承認プロセスの最新情報",
        "category": "FDA・薬事規制",
        "icon": "⚖️",
        "color": "#dc2626",
    },
    {
        "name": "臨床統計ラボ",
        "short_name": "統計",
        "url": "https://pharmaworkerka.github.io/clinical-stats-lab",
        "feed_url": "https://pharmaworkerka.github.io/clinical-stats-lab/feed.xml",
        "description": "統計解析手法・SAS/Rプログラミングの実務テクニック",
        "category": "臨床統計・解析",
        "icon": "📈",
        "color": "#059669",
    },
    {
        "name": "ファーマコビジランス最前線",
        "short_name": "PV",
        "url": "https://pharmaworkerka.github.io/pv-frontline",
        "feed_url": "https://pharmaworkerka.github.io/pv-frontline/feed.xml",
        "description": "安全性情報管理・副作用報告・シグナル検出の専門情報",
        "category": "ファーマコビジランス",
        "icon": "🛡️",
        "color": "#7c3aed",
    },
    {
        "name": "製薬DXジャーナル",
        "short_name": "DX",
        "url": "https://pharmaworkerka.github.io/pharma-dx-journal",
        "feed_url": "https://pharmaworkerka.github.io/pharma-dx-journal/feed.xml",
        "description": "AI創薬・デジタル治験・RWDのDXトレンド最新情報",
        "category": "製薬DX",
        "icon": "🤖",
        "color": "#ea580c",
    },
]

CATEGORIES = [blog["category"] for blog in BLOGS]
