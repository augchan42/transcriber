"""
Cantonese transcription corrections and domain-specific vocabulary prompts.

Post-processing corrections for common Whisper errors on Cantonese content,
plus initial_prompt hints to bias Whisper toward correct domain terminology.

Merged from qdayanon-content-engine's cantonese_corrections.py and domain_prompts.py.
See ADR-058 (Cantonese transcription quality) and ADR-060 (Whisper prompt engineering).
"""

import re
from collections.abc import Callable

# Type alias for replacement - can be string or callable
Replacement = str | Callable[[re.Match], str]

# ---------------------------------------------------------------------------
# Domain-specific correction dictionaries
# ---------------------------------------------------------------------------

ICHING_CORRECTIONS: dict[str, Replacement] = {
    r"液晶": "易經",
    r"河途": "河圖",
    r"九雲": "九運",
    r"離[掛瓜]": "離卦",
    r"乾[掛瓜]": "乾卦",
    r"坤[掛瓜]": "坤卦",
    r"震[掛瓜]": "震卦",
    r"巽[掛瓜]": "巽卦",
    r"坎[掛瓜]": "坎卦",
    r"艮[掛瓜]": "艮卦",
    r"兌[掛瓜]": "兌卦",
    r"憑牛": "畜牝牛",
    r"離[爲為]木": "離為火",
    r"乾[爲為]水": "乾為天",
    r"坤[爲為]火": "坤為地",
    r"王利元吉": "元亨利貞",
    r"([九六][一二三四五初上])岳": lambda m: m.group(1) + "爻",
    r"([九六][一二三四五初上])吵": lambda m: m.group(1) + "爻",
    r"93牛": "九三爻",
    r"93岳": "九三爻",
    r"65吵": "六五爻",
    r"65岳": "六五爻",
    r"94岳": "九四爻",
    r"94吵": "九四爻",
    r"中旅年": "中女運",
    r"上雲": "上運",
    r"下雲": "下運",
}

GEOPOLITICS_CORRECTIONS: dict[str, Replacement] = {
    r"習近憑": "習近平",
    r"拜燈": "拜登",
    r"南還": "南海",
    r"聯促局": "聯儲局",
    r"聯書局": "聯儲局",
}

FINANCE_CORRECTIONS: dict[str, Replacement] = {
    r"騰詢": "騰訊",
    r"阿李巴巴": "阿里巴巴",
    r"家息": "加息",
    r"減希": "減息",
    r"通掌": "通脹",
    r"恆生支數": "恆生指數",
    r"恆深指數": "恆生指數",
}

PARTICLE_CORRECTIONS: dict[str, Replacement] = {
    r"(\s)la(\s|$)": r"\1喇\2",
    r"(\s)ga(\s|$)": r"\1嘅\2",
    r"(\s)ge(\s|$)": r"\1嘅\2",
    r"(\s)ar(\s|$)": r"\1呀\2",
    r"(\s)lo(\s|$)": r"\1囉\2",
    r"(\s)wor(\s|$)": r"\1喎\2",
}

DOMAIN_CORRECTIONS: dict[str, dict[str, Replacement]] = {
    "iching": ICHING_CORRECTIONS,
    "metaphysics": ICHING_CORRECTIONS,
    "geopolitics": GEOPOLITICS_CORRECTIONS,
    "politics": GEOPOLITICS_CORRECTIONS,
    "finance": FINANCE_CORRECTIONS,
    "crypto": FINANCE_CORRECTIONS,
}

UNIVERSAL_CORRECTIONS: dict[str, Replacement] = {
    **PARTICLE_CORRECTIONS,
}

# ---------------------------------------------------------------------------
# Domain-specific Whisper initial_prompt vocabulary hints
# Optimized for 224-token limit with anti-error anchors (ADR-060)
# ---------------------------------------------------------------------------

DOMAIN_PROMPTS: dict[str, str] = {
    "iching": (
        "純粵語轉錄，不要翻譯，不要解釋，只輸出繁體中文。"
        "以下為粵語講解易經：周易 卦 爻 卦辭 爻辭 易傳 "
        "易經（不是液晶） 河圖（不是河途） 洛書 龍馬 神龜 "
        "離卦（不是離掛） 九運（不是九雲） 離為火 "
        "初九 九二 九三 九四 六五 上九 元亨利貞 畜牝牛吉 "
        "乾坤震巽坎離艮兌 三元九運 九宮 飛星 先天 後天"
    ),
    "metaphysics": (
        "純粵語轉錄，不要翻譯，不要解釋，只輸出繁體中文。"
        "以下為粵語講解玄學：風水 八字 紫微斗數 "
        "奇門遁甲 太極 陰陽 五行 八卦 "
        "乾坤震巽坎離艮兌 天干地支 甲乙丙丁戊己庚辛壬癸"
    ),
    "philosophy": (
        "純粵語轉錄，不要翻譯，不要解釋，只輸出繁體中文。"
        "以下為粵語哲學講座：易學 儒家 佛家 道家 儒釋道 "
        "牟宗三 徐復觀 唐君毅 新儒家 朱熹 王陽明 理學 心學 "
        "張載 西銘 為天地立心"
    ),
    "geopolitics": (
        "以下為粵語時事分析：地緣政治 一帶一路 "
        "南海 台海 美中關係 習近平 "
        "中美貿易戰 台灣海峽 九段線 俄烏戰爭"
    ),
    "politics": (
        "以下為粵語政治分析：民主 人權 自由 "
        "選舉 議會 立法會 政府 政策 "
        "一國兩制 基本法 國安法"
    ),
    "finance": (
        "以下為粵語財經分析：恆生指數 騰訊 阿里巴巴 "
        "聯儲局 加息 減息 通脹 滯脹 "
        "人民幣 美元 港元 離岸人民幣 "
        "A股 H股 ADR ETF 期權 期貨"
    ),
    "crypto": (
        "以下為粵語加密貨幣分析：比特幣 以太坊 "
        "虛擬貨幣 區塊鏈 DeFi NFT Web3 "
        "挖礦 錢包 交易所 Binance Coinbase"
    ),
    "technology": (
        "以下為粵語科技分析：人工智能 機器學習 "
        "深度學習 神經網絡 大語言模型 GPT "
        "量子計算 半導體 芯片 晶片"
    ),
    "ai": (
        "以下為粵語人工智能討論：ChatGPT Claude "
        "OpenAI Anthropic Google DeepMind "
        "大語言模型 生成式AI 機器學習 深度學習"
    ),
    "iching_philosophy": (
        "以下為粵語講解易學與儒釋道：易經 周易 卦 爻 卦辭 爻辭 "
        "離卦 離為火 乾坤震巽坎離艮兌 三元九運 九運 洛書 九宮 飛星 "
        "初九 九二 九三 九四 六五 上九 元亨利貞 畜牝牛吉 "
        "朱熹 王陽明 牟宗三 徐復觀 唐君毅 張載 西銘"
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_corrections(text: str, corrections: dict[str, Replacement]) -> str:
    """Apply a set of regex corrections to text."""
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)
    return text


def apply_cantonese_corrections(
    text: str,
    domain: str | None = None,
    apply_universal: bool = True,
) -> str:
    """
    Apply domain-specific and universal corrections to Cantonese transcription.

    Args:
        text: Transcribed text to correct.
        domain: Domain category (e.g., 'iching'). Case-insensitive, comma-separated OK.
        apply_universal: Whether to apply universal particle corrections.
    """
    if not text:
        return text

    if apply_universal:
        text = apply_corrections(text, UNIVERSAL_CORRECTIONS)

    if domain:
        domains = [d.strip().lower() for d in domain.split(",")]
        for d in domains:
            if d in DOMAIN_CORRECTIONS:
                text = apply_corrections(text, DOMAIN_CORRECTIONS[d])

    return text


def get_domain_prompt(category: str | None) -> str | None:
    """
    Get domain-specific vocabulary prompt for Whisper's initial_prompt parameter.

    Args:
        category: Domain category. Case-insensitive, comma-separated for fallback.

    Returns:
        Prompt string optimized for 224-token limit, or None.
    """
    if not category:
        return None

    categories = [c.strip().lower() for c in category.split(",")]
    for cat in categories:
        if cat in DOMAIN_PROMPTS:
            return DOMAIN_PROMPTS[cat]

    return None


def get_available_domains() -> list[str]:
    """Get list of domains with available corrections and/or prompts."""
    return sorted(set(list(DOMAIN_CORRECTIONS.keys()) + list(DOMAIN_PROMPTS.keys())))
