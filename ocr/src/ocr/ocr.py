import cv2
import numpy as np
from PIL import Image
import pytesseract
from pytesseract import Output
from mss import mss
import datetime
from translate import translate_all_blocks  
import asyncio

# Windows環境の場合、Tesseract実行ファイルのパスを指定します。
pytesseract.pytesseract.tesseract_cmd = r"D:\Tesseract-OCR\tesseract.exe"

def capture_screen():
    """
    画面全体をキャプチャし、PIL.Image オブジェクトとして返す関数。
    mssライブラリで高速にキャプチャした後、BGRAからRGBに変換しています。
    """
    with mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
    image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    return image

def perform_ocr(pil_image, conf_threshold=0):
    """
    PIL.Image を入力に、Tesseract OCR で各テキスト領域情報を取得する関数。
    各領域の辞書情報（座標、テキスト、信頼度、ブロック番号）を出力します。
    
    :param pil_image: PIL.Image オブジェクト
    :param conf_threshold: 出力する信頼度の閾値
    :return: OCR結果のリスト（辞書形式）
    """
    # PIL 画像を OpenCV 用BGR画像に変換
    img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    data = pytesseract.image_to_data(img_cv, output_type=Output.DICT)
    
    ocr_results = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        try:
            conf = float(data['conf'][i])
        except ValueError:
            conf = -1
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
    OCR 結果をブロック単位で集約し、テキストとブロック全体の矩形領域を算出する関数。
    
    :param ocr_results: perform_ocr() の戻り値（各テキスト領域の辞書リスト）
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
            blocks[block] = {
                "text": res["text"],
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom
            }
        else:
            blocks[block]["text"] += " " + res["text"]
            blocks[block]["left"] = min(blocks[block]["left"], left)
            blocks[block]["top"] = min(blocks[block]["top"], top)
            blocks[block]["right"] = max(blocks[block]["right"], right)
            blocks[block]["bottom"] = max(blocks[block]["bottom"], bottom)
    
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

def save_captured_image(image, filename=None):
    """
    PIL.Image を指定のファイル名で保存する関数。
    ファイル名が指定されなかった場合は、タイムスタンプを利用した名前を生成します。
    
    :param image: 保存対象の PIL.Image オブジェクト
    :param filename: 保存するファイル名（オプション）
    """
    if filename is None:
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{now}.png"
    image.save(filename)
    print(f"キャプチャ画像を保存しました: {filename}")

def exec_ocr(image):
    """
    画面全体のキャプチャを行い、OCR を実行した結果を
    ブロックごとのテキストと矩形領域の情報として返します。
    
    戻り値:
        aggregated_blocks (dict): 各ブロックの OCR 結果を格納した辞書。
          キーはブロック番号、値は辞書で、
          その中に 'text', 'left', 'top', 'width', 'height' などの情報が含まれます。
    """

    # OCR を実行（信頼度閾値は必要に応じて調整）
    results = perform_ocr(image, conf_threshold=0)
    
    # ブロックごとに認識結果を集約（テキストと矩形座標をまとめる）
    aggregated_blocks = aggregate_results_by_block(results)
    
    return aggregated_blocks

def exec_capture():
    image = capture_screen()
    save_captured_image(image, "cap.png")
    return image

def exec_translate(ocr_data):
    # 辞書の各アイテム（ブロック番号とその情報）に対してループ処理を行います
    updated_data = asyncio.run(translate_all_blocks(ocr_data, update_inplace=True))
    return updated_data

def main():
    # exec_ocr() を呼び出して結果を得る
    aggregated_blocks = exec_ocr()
    
    # 各ブロックのテキストと矩形領域を出力
    for block_num, info in aggregated_blocks.items():
        print(f"ブロック {block_num}:")
        print(f"  テキスト: {info['text']}")
        print(f"  座標: (x: {info['left']}, y: {info['top']}, w: {info['width']}, h: {info['height']})")
        print("-" * 50)


if __name__ == "__main__":
    main()
