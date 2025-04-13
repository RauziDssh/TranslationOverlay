import cv2
import numpy as np
from PIL import Image
import pytesseract
from pytesseract import Output
from mss import mss

# Windows環境の場合、Tesseract実行ファイルのパスを指定します。
pytesseract.pytesseract.tesseract_cmd = r"D:\Tesseract-OCR\tesseract.exe"

def capture_screen():
    """
    画面全体をキャプチャして PIL.Image オブジェクトとして返す関数。
    mss ライブラリを利用して高速キャプチャを実現しています。
    """
    with mss() as sct:
        # 1番目のモニター全体をキャプチャ
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
    
    # mss が返す画像は BGRA 形式なので、Pillow で RGB に変換する
    image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    return image

def perform_ocr(pil_image, conf_threshold=0):
    """
    Pillow の Image オブジェクトを入力として OCR を実行し、
    各テキスト領域（単語または文字）の情報（座標、テキスト、信頼度、ブロック番号）を辞書形式で返す関数。
    
    :param pil_image: PIL.Image オブジェクト
    :param conf_threshold: 信頼度の閾値（0以上の数値、0の場合は全て出力）
    :return: [{'block_num': n, 'left': x, 'top': y, 'width': w, 'height': h, 'text': text, 'conf': conf}, ...]
    """
    # PIL画像を OpenCV 用のBGR画像に変換
    img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # OCR を実行して各領域の情報を辞書形式で取得
    data = pytesseract.image_to_data(img_cv, output_type=Output.DICT)
    
    ocr_results = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        try:
            conf = float(data['conf'][i])
        except ValueError:
            conf = -1  # 信頼度が計算できなかった場合は -1 とする
        
        if text and conf >= conf_threshold:
            bbox = {
                "block_num": data['block_num'][i],
                "left": data['left'][i],
                "top": data['top'][i],
                "width": data['width'][i],
                "height": data['height'][i],
                "text": text,
                "conf": conf,
            }
            ocr_results.append(bbox)
    return ocr_results

def aggregate_results_by_block(ocr_results):
    """
    OCR の結果リストを、block_num ごとにグループ化し、
    各ブロックごとにテキストをまとめ、ブロック矩形（座標・幅・高さ）を算出する関数。
    
    :param ocr_results: perform_ocr() の戻り値（各領域の辞書が入ったリスト）
    :return: { block_num: {'text': 連結テキスト, 'left': x, 'top': y, 'width': w, 'height': h}, ... }
    """
    blocks = {}
    for res in ocr_results:
        block = res["block_num"]
        left = res["left"]
        top = res["top"]
        right = left + res["width"]
        bottom = top + res["height"]
        
        if block not in blocks:
            # 新しいブロックの場合、初期値を設定
            blocks[block] = {
                "text": res["text"],
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom
            }
        else:
            # 既存ブロックにはテキストを連結
            blocks[block]["text"] += " " + res["text"]
            # ブロックの矩形領域を更新（各領域の最小/最大を採用）
            blocks[block]["left"] = min(blocks[block]["left"], left)
            blocks[block]["top"] = min(blocks[block]["top"], top)
            blocks[block]["right"] = max(blocks[block]["right"], right)
            blocks[block]["bottom"] = max(blocks[block]["bottom"], bottom)
    
    # 各ブロックの幅と高さを計算し、出力用の辞書を生成
    aggregated_blocks = {}
    for block, info in blocks.items():
        aggregated_blocks[block] = {
            "text": info["text"],
            "left": info["left"],
            "top": info["top"],
            "width": info["right"] - info["left"],
            "height": info["bottom"] - info["top"]
        }
    return aggregated_blocks

def main():
    # 画面全体のキャプチャ
    image = capture_screen()
    
    # OCR を実行（信頼度閾値は必要に応じて調整）
    results = perform_ocr(image, conf_threshold=0)
    
    # ブロックごとに認識結果を集約（テキストと矩形座標をまとめる）
    aggregated_blocks = aggregate_results_by_block(results)
    
    # 各ブロックのテキストと矩形領域を出力
    for block_num, info in aggregated_blocks.items():
        print(f"ブロック {block_num}:")
        print(f"  テキスト: {info['text']}")
        print(f"  座標: (x: {info['left']}, y: {info['top']}, w: {info['width']}, h: {info['height']})")
        print("-" * 50)

if __name__ == "__main__":
    main()
