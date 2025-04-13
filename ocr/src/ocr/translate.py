import asyncio
from googletrans import Translator

# 非同期に翻訳を実施する関数
async def translate_en_to_ja(text: str) -> str:
    """
    英語のテキストを非同期で日本語に翻訳します。

    Args:
        text (str): 翻訳対象の英語テキスト

    Returns:
        str: 日本語に翻訳されたテキスト
    """
    translator = Translator()
    translation = await translator.translate(text, src='en', dest='ja')
    return translation.text

# 並列に翻訳処理を行い、ocr_dataに結果を書き戻す（update_inplace=True）またはコピーに上書きする（update_inplace=False）関数
async def translate_all_blocks(ocr_data: dict, update_inplace: bool = True) -> dict:
    """
    ocr_data内の各ブロックの英語テキストを並列に日本語へ翻訳し、
    翻訳結果をもとの辞書に書き戻すか、新しい辞書に上書きして返します。

    Args:
        ocr_data (dict): 各ブロックに 'text' キーを含む辞書
        update_inplace (bool, optional): Trueの場合、元の ocr_data を上書きします。
                                         Falseの場合、コピーした辞書に上書きします。
                                         デフォルトはTrue。

    Returns:
        dict: 翻訳結果が反映された辞書（update_inplace が False の場合は新規辞書）
    """
    # update_inplace=False の場合、元のデータをコピーする
    if not update_inplace:
        # 深いコピーを行います。必要に応じて copy.deepcopy() などを利用してください。
        translated_data = {key: value.copy() for key, value in ocr_data.items()}
    else:
        translated_data = ocr_data

    # 各ブロックの翻訳タスクを用意
    async def translate_block(block_num, block_info):
        text_content = block_info.get('text', '')
        translated_text = await translate_en_to_ja(text_content)
        # 今回は 'translated' キーに書き戻す例です。もしくは 'text' を上書きすることも可能です。
        block_info['translated'] = translated_text
        # ※必要に応じて block_info['text'] を上書きするなど調整してください。
        return block_num, translated_text

    tasks = [translate_block(block_num, block_info)
             for block_num, block_info in translated_data.items()]

    # 並列にタスクを実行
    results = await asyncio.gather(*tasks)
    return translated_data

# テスト用のメイン関数
def main():
    # サンプルの OCR データ
    ocr_data = {
        "1": {"text": "Hello, world!"},
        "2": {"text": "This is a test."},
        "3": {"text": "How do you do?"}
    }

    # 並列処理を実行して、更新（またはコピー）後の辞書を受け取る
    updated_data = asyncio.run(translate_all_blocks(ocr_data, update_inplace=True))

    # 各ブロックの結果を表示
    for block_num, block_info in updated_data.items():
        print(f"ブロック {block_num}: {block_info.get('translated')}")

if __name__ == '__main__':
    main()
